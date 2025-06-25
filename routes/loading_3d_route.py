from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import pandas as pd
from werkzeug.utils import secure_filename

loading_3d_bp = Blueprint('loading_3d', __name__)

@loading_3d_bp.route('/loading_3d', methods=['GET', 'POST'])
def loading_3d():
    logs = ''
    summary = None
    detail_table = None
    image_url = None
    if request.method == 'POST':
        file = request.files.get('datafile')
        vehicle_type = request.form.get('vehicle_type')
        strategy = request.form.get('strategy')
        params = request.form.get('params')
        if not file:
            logs = 'Please upload a box data file!'
            return render_template('3d_loading.html', logs=logs)
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.xlsx', '.csv']:
            logs = 'Only Excel or CSV files are supported!'
            return render_template('3d_loading.html', logs=logs)
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        logs = f'File uploaded: {filename}\nVehicle type: {vehicle_type or "-"}\nStrategy: {strategy or "-"}\nParams: {params or "-"}'
        # TODO: Integrate 3D loading algorithm and image generation here
        # Example: summary = "Loading rate: 85%\nTotal boxes: 3"
        # Example: detail_table = pd.DataFrame(...).to_html(...)
        # Example: image_url = url_for('static', filename='img/3d_demo.png')
    return render_template('3d_loading.html', logs=logs, summary=summary, detail_table=detail_table, image_url=image_url)
