from flask import Blueprint, render_template, request, redirect, url_for
import os
import json

package_manage_bp = Blueprint('package_manage', __name__)

PACKAGE_JSON = os.path.join('Dependency', 'Package.json')

@package_manage_bp.route('/package_manage', methods=['GET', 'POST'])
def package_manage():
    # Load all package data
    if not os.path.exists(PACKAGE_JSON):
        packages = {}
    else:
        with open(PACKAGE_JSON, 'r', encoding='utf-8') as f:
            packages = json.load(f)
    message = ''
    # Handle add/edit/delete
    if request.method == 'POST':
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
        # Save changes
        os.makedirs('Dependency', exist_ok=True)
        with open(PACKAGE_JSON, 'w', encoding='utf-8') as f:
            json.dump(packages, f, indent=4)
        return redirect(url_for('package_manage.package_manage'))
    # For GET, show all packages
    # Convert to list of dicts for table
    package_list = [
        {'Package': k, 'Length': v['length'], 'Width': v['width'], 'Height': v['height'], 'Volume': v['volume']}
        for k, v in packages.items()
    ]
    package_list.sort(key=lambda x: x['Package'])
    return render_template('package_manage.html', packages=package_list, message=message)
