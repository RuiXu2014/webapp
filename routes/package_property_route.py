from flask import Blueprint, render_template, request, redirect, url_for
import os
import pandas as pd
import json

package_property_bp = Blueprint('package_property', __name__)

@package_property_bp.route('/package_property', methods=['GET', 'POST'])
def package_property():
    preview = None
    message = ''
    # Load all package data
    package_json = os.path.join('Dependency', 'Package.json')
    if not os.path.exists(package_json):
        all_packages = []
        packages = {}
    else:
        with open(package_json, 'r', encoding='utf-8') as f:
            packages = json.load(f)
        all_packages = [
            {'Package': k, 'Length': v['length'], 'Width': v['width'], 'Height': v['height'], 'Volume': v['volume']}
            for k, v in packages.items()
        ]
        all_packages.sort(key=lambda x: x['Package'])
    # Handle add/delete
    if request.method == 'POST' and request.form.get('action') in ['add', 'delete']:
        action = request.form.get('action')
        if action == 'add':
            pkg = request.form.get('Package')
            length = request.form.get('Length')
            width = request.form.get('Width')
            height = request.form.get('Height')
            volume = request.form.get('Volume')
            if pkg and length and width and height and volume:
                packages[pkg] = {
                    'length': float(length),
                    'width': float(width),
                    'height': float(height),
                    'volume': float(volume)
                }
                message = f'Added/Updated package {pkg}.'
        elif action == 'delete':
            pkg = request.form.get('Package')
            if pkg in packages:
                del packages[pkg]
                message = f'Deleted package {pkg}.'
        os.makedirs('Dependency', exist_ok=True)
        with open(package_json, 'w', encoding='utf-8') as f:
            json.dump(packages, f, indent=4)
        return redirect(url_for('package_property.package_property'))
    # Handle file upload
    if request.method == 'POST' and not request.form.get('action'):
        file = request.files.get('datafile')
        if not file:
            message = 'Please select a file.'
        else:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ['.xlsx', '.xls', '.csv']:
                message = 'Only Excel or CSV files are supported.'
            else:
                try:
                    if ext in ['.xlsx', '.xls']:
                        df = pd.read_excel(file)
                    else:
                        df = pd.read_csv(file)
                    required = ['Package', 'Length', 'Width', 'Height', 'Volume']
                    missing = [col for col in required if col not in df.columns]
                    if missing:
                        message = f'Missing columns: {", ".join(missing)}'
                    else:
                        preview = df[required].head(5).to_dict(orient='records')
                        os.makedirs('Dependency', exist_ok=True)
                        package_data = {
                            str(row['Package']): {
                                'length': float(row['Length']),
                                'width': float(row['Width']),
                                'height': float(row['Height']),
                                'volume': float(row['Volume'])
                            }
                            for _, row in df.iterrows()
                        }
                        with open(package_json, 'w', encoding='utf-8') as f:
                            json.dump(package_data, f, indent=4)
                        message = f"Saved {len(package_data)} packages to Dependency/Package.json"
                        # Update all_packages for display
                        all_packages = [
                            {'Package': k, 'Length': v['length'], 'Width': v['width'], 'Height': v['height'], 'Volume': v['volume']}
                            for k, v in package_data.items()
                        ]
                        all_packages.sort(key=lambda x: x['Package'])
                except Exception as e:
                    message = f'Error: {str(e)}'
    return render_template('package_property.html', preview=preview, message=message, all_packages=all_packages)
