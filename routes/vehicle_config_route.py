import os
import json
from flask import Blueprint, render_template, request, jsonify
import requests

vehicle_config_bp = Blueprint('vehicle_config', __name__)

VEHICLE_CONFIG_PATH = os.path.join('configs', 'vehicle_templates.json')

@vehicle_config_bp.route('/vehicle_config', methods=['GET', 'POST'])
def vehicle_config():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        size = data.get('size')
        if not name or not size:
            return jsonify({'success': False, 'msg': 'Name and size required'}), 400
        if os.path.exists(VEHICLE_CONFIG_PATH):
            with open(VEHICLE_CONFIG_PATH, 'r', encoding='utf-8') as f:
                vehicles = json.load(f)
        else:
            vehicles = {}
        vehicles[name] = {'size': size}
        with open(VEHICLE_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(vehicles, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    # GET
    if os.path.exists(VEHICLE_CONFIG_PATH):
        with open(VEHICLE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            vehicles = json.load(f)
    else:
        vehicles = {}
    return render_template('vehicle_config.html', vehicles=vehicles)

@vehicle_config_bp.route('/vehicle_config/api/list')
def vehicle_list():
    if os.path.exists(VEHICLE_CONFIG_PATH):
        with open(VEHICLE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            vehicles = json.load(f)
    else:
        vehicles = {}
    return jsonify(list(vehicles.keys()))

@vehicle_config_bp.route('/vehicle_config/api/<name>')
def vehicle_detail(name):
    if os.path.exists(VEHICLE_CONFIG_PATH):
        with open(VEHICLE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            vehicles = json.load(f)
    else:
        vehicles = {}
    return jsonify(vehicles.get(name, {}))

@vehicle_config_bp.route('/vehicle_config/api/delete', methods=['POST'])
def vehicle_delete():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'msg': 'Name required'}), 400
    if os.path.exists(VEHICLE_CONFIG_PATH):
        with open(VEHICLE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            vehicles = json.load(f)
    else:
        vehicles = {}
    if name in vehicles:
        vehicles.pop(name)
        with open(VEHICLE_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(vehicles, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    return jsonify({'success': False, 'msg': 'Truck not found'}), 404

@vehicle_config_bp.route('/vehicle_config/api/update', methods=['POST'])
def vehicle_update():
    data = request.get_json()
    name = data.get('name')
    size = data.get('size')
    if not name or not size:
        return jsonify({'success': False, 'msg': 'Name and size required'}), 400
    if os.path.exists(VEHICLE_CONFIG_PATH):
        with open(VEHICLE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            vehicles = json.load(f)
    else:
        vehicles = {}
    if name in vehicles:
        vehicles[name]['size'] = size
        with open(VEHICLE_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(vehicles, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    return jsonify({'success': False, 'msg': 'Truck not found'}), 404

@vehicle_config_bp.route('/assistant_chat', methods=['POST'])
def assistant_chat():
    import traceback
    data = request.get_json()
    user_msg = data.get('message', '')
    try:
        # Tencent Hunyuan HTTP API (see https://cloud.tencent.com/document/product/1729/111007)
        url = "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"
        api_key = "sk-yyavZYlHiRSSPRIUVhWe9hD4qc11n2x8IUVTFq5tWXOyXB8D"  # Replace with your actual API key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "hunyuan-lite",
            "messages": [
                {"role": "user", "content": user_msg}
            ]
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            result = resp.json()
            # According to docs, choices[n]["message"]["content"] is for normal reply
            if "choices" in result and result["choices"]:
                choice = result["choices"][0]
                # Defensive: check for both 'message' and 'content' at top level
                if "message" in choice and "content" in choice["message"]:
                    reply = choice["message"]["content"]
                elif "content" in choice:
                    reply = choice["content"]
                else:
                    reply = str(choice)
            else:
                reply = "No response."
        else:
            reply = f"API Error: {resp.status_code} {resp.text}"
    except Exception as e:
        reply = f'Error: {str(e)}\n{traceback.format_exc()}'
    return jsonify({'reply': reply})
