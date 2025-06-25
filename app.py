from flask import Flask, render_template
from routes.configuration_route import configuration_bp
from routes.loading_route import loading_bp
from routes.radio_detail_route import radio_detail_bp
from routes.training_route import training_bp
from routes.prediction_route import prediction_bp
from routes.loading_3d_route import loading_3d_bp
from routes.package_property_route import package_property_bp
from routes.vehicle_config_route import vehicle_config_bp
import os
import json
from flask import request, jsonify

app = Flask(__name__)
app.register_blueprint(configuration_bp)
app.register_blueprint(loading_bp)
app.register_blueprint(radio_detail_bp)
app.register_blueprint(training_bp)
app.register_blueprint(prediction_bp)
app.register_blueprint(loading_3d_bp)
app.register_blueprint(package_property_bp)
app.register_blueprint(vehicle_config_bp)

CONTAINER_DIR = os.path.join(os.path.dirname(__file__), 'container_data')
os.makedirs(CONTAINER_DIR, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/container_config', methods=['GET', 'POST'])
def container_config():
    # 这里假设有container_templates变量，实际可根据你的业务逻辑调整
    container_templates = {}
    return render_template('container_config.html', container_templates=container_templates)

@app.route('/vehicle_config', methods=['GET', 'POST'])
def vehicle_config():
    # 这里假设有vehicle_templates变量，实际可根据你的业务逻辑调整
    vehicle_templates = {}
    return render_template('vehicle_config.html', vehicle_templates=vehicle_templates)

@app.route('/container_config/api/list', methods=['GET'])
def list_containers():
    files = [f for f in os.listdir(CONTAINER_DIR) if f.endswith('.json')]
    names = [os.path.splitext(f)[0] for f in files]
    return jsonify(names)

@app.route('/container_config/api/<name>', methods=['GET'])
def get_container(name):
    path = os.path.join(CONTAINER_DIR, f'{name}.json')
    if not os.path.exists(path):
        return jsonify({'error': 'not found'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/container_config/api', methods=['POST'])
def add_container():
    name = request.json.get('name')
    size = request.json.get('size')
    if not name:
        return jsonify({'error': 'name required'}), 400
    path = os.path.join(CONTAINER_DIR, f'{name}.json')
    if os.path.exists(path):
        return jsonify({'error': 'already exists'}), 400
    data = {'name': name, 'size': size, 'bins': []}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True})

@app.route('/container_config/api/<name>', methods=['DELETE'])
def delete_container(name):
    path = os.path.join(CONTAINER_DIR, f'{name}.json')
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'success': True})
    return jsonify({'error': 'not found'}), 404

@app.route('/container_config/api/<name>/bin', methods=['POST'])
def add_bin(name):
    path = os.path.join(CONTAINER_DIR, f'{name}.json')
    if not os.path.exists(path):
        return jsonify({'error': 'container not found'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    bin_data = request.json
    data['bins'].append(bin_data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True})

@app.route('/container_config/api/<name>/bin/<int:index>', methods=['DELETE'])
def delete_bin(name, index):
    path = os.path.join(CONTAINER_DIR, f'{name}.json')
    if not os.path.exists(path):
        return jsonify({'error': 'container not found'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['bins'] = [b for b in data['bins'] if b.get('index') != index]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run()
    #app.run(host="172.16.115.158", port=8000, ssl_context=("self.crt", "self.key"))
    #app.run(debug=True)

