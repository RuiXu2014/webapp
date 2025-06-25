from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import json

def get_radio_materials():
    radio_json_path = os.path.join('output_json', 'Radio_packaging_data.json')
    if os.path.exists(radio_json_path):
        with open(radio_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

radio_detail_bp = Blueprint('radio_detail', __name__)

@radio_detail_bp.route('/radio_detail/<path:material_id>', methods=['GET', 'POST'])
def radio_detail(material_id):
    radio_materials = get_radio_materials()
    if not radio_materials:
        flash('未找到Radio数据')
        return redirect(url_for('loading.loading'))
    if material_id not in radio_materials:
        flash('未找到该材料')
        return redirect(url_for('loading.loading'))
    data = radio_materials[material_id]
    if request.method == 'POST':
        records = []
        min_quantity = float('inf')
        max_quantity = float('-inf')
        for i in range(len(request.form.getlist('packed_quantity'))):
            try:
                packed_quantity = int(request.form.getlist('packed_quantity')[i])
                packaging_materials = request.form.getlist('packaging_materials')[i]
                length = float(request.form.getlist('length')[i])
                width = float(request.form.getlist('width')[i])
                height = float(request.form.getlist('height')[i])
                total_volume = float(request.form.getlist('total_volume')[i])
                is_min = 'is_min_%d' % i in request.form
                is_max = 'is_max_%d' % i in request.form
                min_quantity = min(min_quantity, packed_quantity)
                max_quantity = max(max_quantity, packed_quantity)
                records.append({
                    'packed_quantity': packed_quantity,
                    'packaging_materials': packaging_materials,
                    'length': length,
                    'width': width,
                    'height': height,
                    'total_volume': total_volume,
                    'is_min': is_min,
                    'is_max': is_max
                })
            except Exception:
                continue
        data = {
            'min_quantity': int(min_quantity) if records else 0,
            'max_quantity': int(max_quantity) if records else 0,
            'unique_records_count': len(records),
            'records': records
        }
        radio_materials[material_id] = data
        radio_json_path = os.path.join('output_json', 'Radio_packaging_data.json')
        with open(radio_json_path, 'w', encoding='utf-8') as f:
            json.dump(radio_materials, f, indent=4, ensure_ascii=False)
        flash('保存成功')
        return redirect(url_for('radio_detail.radio_detail', material_id=material_id))
    return render_template('radio_detail.html', material_id=material_id, data=data)

@radio_detail_bp.route('/delete_radio_material/<path:material_id>')
def delete_radio_material(material_id):
    radio_materials = get_radio_materials()
    if not radio_materials:
        flash('未找到Radio数据')
        return redirect(url_for('loading.loading'))
    if material_id in radio_materials:
        del radio_materials[material_id]
        radio_json_path = os.path.join('output_json', 'Radio_packaging_data.json')
        with open(radio_json_path, 'w', encoding='utf-8') as f:
            json.dump(radio_materials, f, indent=4, ensure_ascii=False)
        flash('已删除')
    return redirect(url_for('loading.loading'))
