from flask import Blueprint, render_template, request, send_file, jsonify
import os
import json
import pandas as pd
import pickle
import uuid

def load_shipping_points():
    SHIPPING_POINTS_FILE = 'shipping_points.json'
    if not os.path.exists(SHIPPING_POINTS_FILE):
        return []
    with open(SHIPPING_POINTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def handle_radio_prediction(material, qty, radio_data):
    if material not in radio_data:
        return [default_prediction(qty)]
    material_data = radio_data[material]
    records = material_data['records']
    max_quantity = material_data['max_quantity']
    quantity_map = {r['packed_quantity']: r for r in records}
    if qty in quantity_map:
        return [quantity_map[qty]]
    if qty > max_quantity:
        return split_order(material, qty, material_data)
    sorted_records = sorted(records, key=lambda x: x['packed_quantity'])
    idx = next((i for i, r in enumerate(sorted_records) if r['packed_quantity'] >= qty), len(sorted_records)-1)
    return [sorted_records[idx]]

def split_order(material, total_qty, material_data):
    records = material_data['records']
    max_quantity = material_data['max_quantity']
    max_record = next(r for r in records if r['packed_quantity'] == max_quantity)
    packages = []
    remaining_qty = total_qty
    while remaining_qty >= max_quantity:
        packages.append(max_record)
        remaining_qty -= max_quantity
    quantity_map = {r['packed_quantity']: r for r in records}
    if remaining_qty > 0:
        if remaining_qty in quantity_map:
            packages.append(quantity_map[remaining_qty])
        elif 1 in quantity_map:
            single_package = quantity_map[1]
            for _ in range(remaining_qty):
                packages.append(single_package)
        else:
            packages.append(default_prediction(remaining_qty))
    return packages

def default_prediction(qty):
    return {
        'packaging_materials': "未知",
        'length': 0.0,
        'width': 0.0,
        'height': 0.0,
        'total_volume': 0.0,
        'packed_quantity': qty
    }

def handle_site_prediction(materials, qtys, model_pipeline, radio_data):
    feature_columns = model_pipeline['preprocessor']['feature_columns']
    class_model = model_pipeline['classification']
    reg_model = model_pipeline['regression']
    label_encoder = model_pipeline.get('label_encoder')
    # 构造Bag of Materials特征 + 总数量 + 物料种类数
    base_features = {col: 0 for col in feature_columns}
    total_qty = 0
    type_count = 0
    for material, qty in zip(materials, qtys):
        if material in base_features:
            base_features[material] += qty
    # 计算总数量和种类数
    material_cols = [col for col in feature_columns if col not in ('Total_Packed_Quantity', 'Material_Type_Count')]
    total_qty = sum([base_features[col] for col in material_cols])
    type_count = sum([1 for col in material_cols if base_features[col] > 0])
    if 'Total_Packed_Quantity' in base_features:
        base_features['Total_Packed_Quantity'] = total_qty
    if 'Material_Type_Count' in base_features:
        base_features['Material_Type_Count'] = type_count
    feature_df = pd.DataFrame([base_features])[feature_columns]
    material_pred_num = class_model.predict(feature_df)[0]
    if label_encoder is not None:
        material_pred = label_encoder.inverse_transform([material_pred_num])[0]
    else:
        material_pred = material_pred_num
    dim_pred = reg_model.predict(feature_df)[0]
    length = round(dim_pred[0], 2)
    width = round(dim_pred[1], 2)
    height = round(dim_pred[2], 2)
    total_volume = round(length * width * height, 2)
    material_details = [
        {"material": mat, "quantity": qty}
        for mat, qty in zip(materials, qtys)
    ]
    return [{
        'packaging_materials': material_pred,
        'length': length,
        'width': width,
        'height': height,
        'total_volume': total_volume,
        'total_packed_quantity': total_qty,
        'material_quantities': material_details,
        'package_match': False,
        'note': ''
    }]

def run_prediction(data_frame, model_pipeline, radio_data, shipping_config):
    required_columns = ['SD Document', 'Shipping Point', 'Material', 'Qty']
    if not all(col in data_frame.columns for col in required_columns):
        raise ValueError("Missing required columns: " + ', '.join(required_columns))
    df = data_frame.copy()
    results = []
    # Load package info for site material
    try:
        with open(os.path.join('Dependency', 'Package.json'), 'r', encoding='utf-8') as f:
            package_info = json.load(f)
    except Exception:
        package_info = {}
    # Group by SD Document for all rows
    grouped_orders = df.groupby('SD Document').agg({
        'Material': list,
        'Qty': list,
        'Shipping Point': 'first'
    })
    for doc_id, group in grouped_orders.iterrows():
        materials = group['Material']
        qtys = group['Qty']
        shipping_point = group['Shipping Point']
        material_class = shipping_config.get(str(shipping_point).upper(), '').lower()
        # SiteMaterial logic
        if material_class == 'sitematerial':
            predictions = handle_site_prediction(materials, qtys, model_pipeline, radio_data)
            for prediction in predictions:
                material_str = ", ".join(
                    f"{item['material']}:{item['quantity']}" 
                    for item in prediction['material_quantities']
                )
                result_row = {
                    'SD Document': doc_id,
                    'Shipping Point': shipping_point,
                    'Material': material_str,
                    'Qty': sum(qtys),
                    'Packaging': prediction['packaging_materials'],
                    'Length': prediction['length'],
                    'Width': prediction['width'],
                    'Height': prediction['height'],
                    'Volume': prediction['total_volume']
                }
                # Update by package_info if available
                pkg_no = str(prediction['packaging_materials'])
                pkg_data = package_info.get(pkg_no)
                if pkg_data:
                    result_row['Length'] = pkg_data.get('length', result_row['Length'])
                    result_row['Width'] = pkg_data.get('width', result_row['Width'])
                    result_row['Height'] = pkg_data.get('height', result_row['Height'])
                    result_row['Volume'] = pkg_data.get('volume', result_row['Volume'])
                results.append(result_row)
        else:
            # Radio/Other logic
            for material, qty in zip(materials, qtys):
                predictions = handle_radio_prediction(material, qty, radio_data)
                for pack in predictions:
                    result_row = {
                        'SD Document': doc_id,
                        'Shipping Point': shipping_point,
                        'Material': material,
                        'Qty': pack['packed_quantity'],
                        'Packaging': pack['packaging_materials'],
                        'Length': pack['length'],
                        'Width': pack['width'],
                        'Height': pack['height'],
                        'Volume': pack['total_volume']
                    }
                    results.append(result_row)
    return pd.DataFrame(results)

prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('/prediction', methods=['GET', 'POST'])
def prediction():
    models_dir = 'models'
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
    preview_html = None
    logs = ''
    selected_model = None
    result_table_html = None
    download_id = None
    if request.method == 'POST':
        try:
            selected_model = request.form.get('model_file')
            data_file = request.files.get('data_file')
            if not selected_model or not data_file:
                logs = 'Please select a model and upload a prediction data file!'
                return render_template('prediction.html', model_files=model_files, selected_model=selected_model, preview_html=None, result_table_html=None, logs=logs, download_id=None)
            model_path = os.path.join(models_dir, selected_model)
            data_path = os.path.join('uploads', 'predict_data.csv')
            if data_file.filename.endswith('.csv'):
                data_file.save(data_path)
                df = pd.read_csv(data_path)
            else:
                data_path = os.path.join('uploads', 'predict_data.xlsx')
                data_file.save(data_path)
                df = pd.read_excel(data_path)
            if not df.empty:
                preview_html = df.head(10).to_html(classes='table table-striped', index=False)
            else:
                preview_html = None
            with open(model_path, 'rb') as f:
                model_pipeline = pickle.load(f)
            radio_json_path = os.path.join('output_json', 'Radio_packaging_data.json')
            if os.path.exists(radio_json_path):
                with open(radio_json_path, 'r', encoding='utf-8') as f:
                    radio_data = json.load(f)
            else:
                radio_data = {}
            config = load_shipping_points()
            shipping_config = {str(item.get('shipping_point', item.get('Shipping Point', '')).upper()): item.get('material_class', item.get('Material Class', '')) for item in config}
            results_df = run_prediction(df, model_pipeline, radio_data, shipping_config)
            if not results_df.empty:
                # 用id="prediction-table"以便前端分页
                result_table_html = results_df.to_html(classes='table table-bordered', index=False, table_id='prediction-table')
                logs = f'Prediction complete, {len(results_df)} results.'
                download_id = str(uuid.uuid4())
                download_path = os.path.join('uploads', f'prediction_{download_id}.csv')
                results_df.to_csv(download_path, index=False, encoding='utf-8-sig')
            else:
                result_table_html = None
                logs = 'No prediction results.'
                download_id = None
        except Exception as e:
            logs = f'Prediction failed: {str(e)}'
            result_table_html = None
            download_id = None
    return render_template('prediction.html', model_files=model_files, selected_model=selected_model, preview_html=preview_html, result_table_html=result_table_html, logs=logs, download_id=download_id)

@prediction_bp.route('/download_prediction/<download_id>')
def download_prediction(download_id):
    download_path = os.path.join('uploads', f'prediction_{download_id}.csv')
    if os.path.exists(download_path):
        return send_file(download_path, as_attachment=True, download_name='prediction_result.csv')
    else:
        return 'File does not exist or has expired', 404

@prediction_bp.route('/yuanbao_chat', methods=['POST'])
def yuanbao_chat():
    # Replace with your actual Tencent Yuanbao API call
    import requests
    data = request.get_json()
    user_msg = data.get('message', '')
    # --- Tencent Yuanbao API integration ---
    # Example: Replace the following with your real API endpoint and credentials
    api_url = 'https://yuanbao.tencent.com/api/chat'  # Placeholder
    api_key = 'YOUR_TENCENT_YUANBAO_API_KEY'  # Replace with your key
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {
        'query': user_msg,
        # Add any required parameters for Yuanbao API here
    }
    try:
        # resp = requests.post(api_url, headers=headers, json=payload, timeout=10)
        # reply = resp.json().get('reply', 'Sorry, no response.')
        # For demo, just echo the message
        reply = f"[Assistant] {user_msg}"
    except Exception as e:
        reply = f"Error: {str(e)}"
    return jsonify({'reply': reply})
