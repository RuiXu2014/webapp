# This file was merged into routes/loading_3d_route.py. All logic is now in the blueprint.
# This file is kept as a placeholder and should be deleted if not needed.

# 3D装载算法与可视化的后端逻辑可在此完善
# 当前仅做页面跳转和参数收集，未集成实际装载算法
import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from app import app

@app.route('/loading_3d', methods=['GET', 'POST'])
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
            logs = '请上传订单数据文件！'
            return render_template('3d_loading.html', logs=logs)
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.xlsx', '.csv']:
            logs = '仅支持Excel或CSV文件！'
            return render_template('3d_loading.html', logs=logs)
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        logs = f'文件已上传: {filename}\n车型: {vehicle_type or "-"}\n策略: {strategy or "-"}\n参数: {params or "-"}'
        # TODO: 这里可集成3D装载算法与图片生成
        # 示例：summary = "装载率: 85%\n总箱数: 3"
        # 示例：detail_table = pd.DataFrame(...).to_html(...)
        # 示例：image_url = url_for('static', filename='img/3d_demo.png')
    return render_template('3d_loading.html', logs=logs, summary=summary, detail_table=detail_table, image_url=image_url)
