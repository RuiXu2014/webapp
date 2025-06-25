from flask import Blueprint, render_template, request, redirect, url_for, flash
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

def save_shipping_points(data):
    SHIPPING_POINTS_FILE = 'shipping_points.json'
    with open(SHIPPING_POINTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

configuration_bp = Blueprint('configuration', __name__)

@configuration_bp.route('/configuration', methods=['GET', 'POST'])
def configuration():
    shipping_points = load_shipping_points()
    material_classes = ['Radio', 'SiteMaterial', 'Others']
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            shipping_point = request.form.get('shipping_point', '').strip()
            material_class = request.form.get('material_class', '').strip()
            if shipping_point and material_class:
                shipping_points.append({'shipping_point': shipping_point, 'material_class': material_class})
                save_shipping_points(shipping_points)
        elif action == 'edit':
            idx = int(request.form.get('idx', -1))
            shipping_point = request.form.get('shipping_point', '').strip()
            material_class = request.form.get('material_class', '').strip()
            if 0 <= idx < len(shipping_points) and shipping_point and material_class:
                shipping_points[idx] = {'shipping_point': shipping_point, 'material_class': material_class}
                save_shipping_points(shipping_points)
        elif action == 'delete':
            idx = int(request.form.get('idx', -1))
            if 0 <= idx < len(shipping_points):
                shipping_points.pop(idx)
                save_shipping_points(shipping_points)
        return redirect(url_for('configuration.configuration'))
    return render_template('configuration.html', shipping_points=shipping_points, material_classes=material_classes)
