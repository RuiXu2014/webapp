from flask import Blueprint, render_template, request
import os
import json
import pandas as pd
from werkzeug.utils import secure_filename

def load_shipping_points():
    SHIPPING_POINTS_FILE = 'shipping_points.json'
    if not os.path.exists(SHIPPING_POINTS_FILE):
        return []
    with open(SHIPPING_POINTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_radio_data(df, output_path):
    logs = []
    column_mapping = {
        'Material': ['Material'],
        'Packed Quantity': ['Packed Quantity', 'PackedQty', 'Qty'],
        'Packaging Materials': ['Packaging Materials', 'Packaging'],
        'Length': ['Length'],
        'Width': ['Width'],
        'Height': ['Height'],
        'Total Volume': ['Total Volume', 'Volume']
    }
    for standard_name, possible_names in column_mapping.items():
        for name in possible_names:
            if name in df.columns:
                df.rename(columns={name: standard_name}, inplace=True)
                break
    required_columns = list(column_mapping.keys())
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logs.append(f"缺少必要列: {', '.join(missing_columns)}")
        return logs
    df = df[required_columns]
    material_data = {}
    for material, group in df.groupby('Material'):
        quantity_group = group.drop_duplicates(subset=['Packed Quantity'], keep='first')
        min_qty = quantity_group['Packed Quantity'].min()
        max_qty = quantity_group['Packed Quantity'].max()
        records = []
        for _, row in quantity_group.iterrows():
            packed_qty = row['Packed Quantity']
            records.append({
                'packed_quantity': int(packed_qty),
                'is_min': bool(packed_qty == min_qty),
                'is_max': bool(packed_qty == max_qty),
                'packaging_materials': row['Packaging Materials'],
                'length': float(row['Length']),
                'width': float(row['Width']),
                'height': float(row['Height']),
                'total_volume': float(row['Total Volume'])
            })
        records.sort(key=lambda x: x['packed_quantity'])
        material_data[material] = {
            'min_quantity': int(min_qty),
            'max_quantity': int(max_qty),
            'unique_records_count': len(records),
            'records': records
        }
    output_file = os.path.join(output_path, 'Radio_packaging_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(material_data, f, indent=4, ensure_ascii=False)
    logs.append(f"Radio/Others数据已保存: {output_file} (共{len(material_data)}种材料)")
    return logs

def process_sm_data(df, output_path):
    logs = []
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_path, f'cnd7_data_{timestamp}.csv')
    df.to_csv(output_file, index=False)
    logs.append(f"SiteMaterial数据已保存为CSV: {output_file}")
    return logs

loading_bp = Blueprint('loading', __name__)

@loading_bp.route('/loading', methods=['GET', 'POST'])
def loading():
    logs = []
    radio_materials = None
    if request.method == 'POST':
        file = request.files.get('datafile')
        if not file:
            logs.append('未选择文件')
            return render_template('loading.html', logs='\n'.join(logs))
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.xlsx', '.csv']:
            logs.append('仅支持Excel或CSV文件')
            return render_template('loading.html', logs='\n'.join(logs))
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        logs.append(f'文件已上传: {filename}')
        try:
            if ext == '.xlsx':
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)
            if 'Shipping Point' not in df.columns:
                logs.append("数据文件中缺少'Shipping Point'列")
                return render_template('loading.html', logs='\n'.join(logs))
            config = load_shipping_points()
            shipping_config = {str(item.get('shipping_point', item.get('Shipping Point', '')).upper()): item.get('material_class', item.get('Material Class', '')) for item in config}
            json_path = 'output_json'
            csv_path = 'output_csv'
            os.makedirs(json_path, exist_ok=True)
            os.makedirs(csv_path, exist_ok=True)
            radio_points = [k for k, v in shipping_config.items() if v == 'Radio' or v == 'Others']
            if radio_points:
                logs.append(f"配置为'Radio'或'Others'的Shipping Point: {radio_points}")
                radio_df = df[df['Shipping Point'].str.upper().isin(radio_points)]
                if not radio_df.empty:
                    logs.append('处理Radio/Others数据...')
                    logs += process_radio_data(radio_df, json_path)
            sm_points = [k for k, v in shipping_config.items() if v == 'SiteMaterial']
            if sm_points:
                logs.append(f"配置为'SiteMaterial'的Shipping Point: {sm_points}")
                sm_df = df[df['Shipping Point'].str.upper().isin(sm_points)]
                if not sm_df.empty:
                    logs.append('处理SiteMaterial数据...')
                    logs += process_sm_data(sm_df, csv_path)
            logs.append('历史数据处理完成!')
        except Exception as e:
            logs.append(f'处理失败: {str(e)}')
    radio_json_path = os.path.join('output_json', 'Radio_packaging_data.json')
    if os.path.exists(radio_json_path):
        with open(radio_json_path, 'r', encoding='utf-8') as f:
            radio_materials = json.load(f)
    return render_template('loading.html', logs='\n'.join(logs) if logs else None, radio_materials=radio_materials)

@loading_bp.route('/update_radio_material', methods=['POST'])
def update_radio_material():
    try:
        data = request.get_json()
        material_id = data.get('material_id')
        records = data.get('records')
        radio_json_path = os.path.join('output_json', 'Radio_packaging_data.json')
        if not os.path.exists(radio_json_path):
            return {'success': False, 'msg': 'Radio packaging data not found.'}, 404
        with open(radio_json_path, 'r', encoding='utf-8') as f:
            radio_data = json.load(f)
        if material_id not in radio_data:
            return {'success': False, 'msg': 'Material not found.'}, 404
        radio_data[material_id]['records'] = records
        # Update min/max/unique_records_count based on new records
        if records:
            min_qty = min(r['packed_quantity'] for r in records)
            max_qty = max(r['packed_quantity'] for r in records)
            radio_data[material_id]['min_quantity'] = min_qty
            radio_data[material_id]['max_quantity'] = max_qty
            radio_data[material_id]['unique_records_count'] = len(records)
        with open(radio_json_path, 'w', encoding='utf-8') as f:
            json.dump(radio_data, f, indent=4, ensure_ascii=False)
        return {'success': True, 'msg': 'Material records updated successfully.'}
    except Exception as e:
        return {'success': False, 'msg': str(e)}, 500

@loading_bp.route('/delete_radio_material', methods=['POST'])
def delete_radio_material():
    try:
        data = request.get_json()
        material_id = data.get('material_id')
        radio_json_path = os.path.join('output_json', 'Radio_packaging_data.json')
        if not os.path.exists(radio_json_path):
            return {'success': False, 'msg': 'Radio packaging data not found.'}, 404
        with open(radio_json_path, 'r', encoding='utf-8') as f:
            radio_data = json.load(f)
        if material_id not in radio_data:
            return {'success': False, 'msg': 'Material not found.'}, 404
        del radio_data[material_id]
        with open(radio_json_path, 'w', encoding='utf-8') as f:
            json.dump(radio_data, f, indent=4, ensure_ascii=False)
        return {'success': True, 'msg': 'Material deleted successfully.'}
    except Exception as e:
        return {'success': False, 'msg': str(e)}, 500

@loading_bp.route('/radio_material_detail/<path:material_id>')
def radio_material_detail(material_id):
    import os, json
    radio_json_path = os.path.join('output_json', 'Radio_packaging_data.json')
    records = []
    if os.path.exists(radio_json_path):
        with open(radio_json_path, 'r', encoding='utf-8') as f:
            radio_data = json.load(f)
        if material_id in radio_data:
            records = radio_data[material_id].get('records', [])
    return render_template('radio_material_detail.html', material_id=material_id, records=records)
