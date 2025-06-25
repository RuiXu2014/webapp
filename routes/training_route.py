from flask import Blueprint, render_template, request
import os
import pandas as pd
import numpy as np
import pickle
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import classification_report, mean_squared_error, mean_absolute_error, r2_score, accuracy_score
from sklearn.preprocessing import LabelEncoder
import datetime

def load_shipping_points():
    SHIPPING_POINTS_FILE = 'shipping_points.json'
    if not os.path.exists(SHIPPING_POINTS_FILE):
        return []
    with open(SHIPPING_POINTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

training_bp = Blueprint('training', __name__)

@training_bp.route('/training', methods=['GET', 'POST'])
def training():
    csv_path = 'output_csv'
    datasets = [f for f in os.listdir(csv_path) if f.startswith('cnd7_data_') and f.endswith('.csv')]
    logs = ''
    results = ''
    # Default config for web: use first dataset, default fields, sum aggregation, classification
    default_dataset = datasets[0] if datasets else ''
    default_group_by = 'HU number'
    default_features = ['Material', 'Packed Quantity']
    default_agg = 'sum'
    model_type = 'classification'  # or 'regression'
    if request.method == 'POST':
        try:
            dataset = request.form.get('dataset', default_dataset)
            group_by = request.form.get('group_by', default_group_by)
            features = request.form.getlist('features') or default_features
            agg = request.form.get('agg', default_agg)
            n_estimators = int(request.form.get('n_estimators', 200))
            max_depth = int(request.form.get('max_depth', 10))
            min_samples_split = int(request.form.get('min_samples_split', 2))
            min_samples_leaf = int(request.form.get('min_samples_leaf', 1))
            train_ratio = float(request.form.get('train_ratio', 80)) / 100
            random_state = 42
            max_features = request.form.get('max_features', 'sqrt')
            if max_features == 'None':
                max_features = None
            bootstrap = request.form.get('bootstrap', 'True') == 'True'
            logs_list = []
            logs_list.append(f"Training started: selected dataset {dataset}")
            file_path = os.path.join(csv_path, dataset)
            df = pd.read_csv(file_path)
            def load_and_preprocess_data(df, features, group_by, aggregation_operation):
                required_columns = features + ['Packaging Materials', 'Length', 'Width', 'Height']
                missing_cols = [col for col in required_columns if col not in df.columns]
                if missing_cols:
                    raise ValueError(f"Missing columns in the data: {missing_cols}")
                df = df.dropna(subset=required_columns)
                numeric_features = [f for f in features if df[f].dtype in ['int64', 'float64']]
                df[numeric_features] = df[numeric_features].apply(pd.to_numeric, errors='coerce')
                df = df.dropna(subset=numeric_features)
                categorical_features = [f for f in features if f not in numeric_features]
                df_with_dummies = pd.get_dummies(df, columns=categorical_features)
                if aggregation_operation == 'sum':
                    df_aggregated = df_with_dummies.groupby(group_by).sum(numeric_only=True).reset_index()
                elif aggregation_operation == 'mean':
                    df_aggregated = df_with_dummies.groupby(group_by).mean(numeric_only=True).reset_index()
                elif aggregation_operation == 'max':
                    df_aggregated = df_with_dummies.groupby(group_by).max().reset_index()
                elif aggregation_operation == 'min':
                    df_aggregated = df_with_dummies.groupby(group_by).min().reset_index()
                elif aggregation_operation == 'median':
                    df_aggregated = df_with_dummies.groupby(group_by).median(numeric_only=True).reset_index()
                elif aggregation_operation == 'std':
                    df_aggregated = df_with_dummies.groupby(group_by).std(numeric_only=True).reset_index()
                elif aggregation_operation == 'count':
                    df_aggregated = df_with_dummies.groupby(group_by).count().reset_index()
                elif aggregation_operation == 'product':
                    df_aggregated = df_with_dummies.groupby(group_by).prod(numeric_only=True).reset_index()
                else:
                    raise ValueError(f"Unknown aggregation: {aggregation_operation}")
                df_aggregated['Packaging Materials'] = df.groupby(group_by)['Packaging Materials'].first().values
                df_aggregated['Length'] = df.groupby(group_by)['Length'].first().values
                df_aggregated['Width'] = df.groupby(group_by)['Width'].first().values
                df_aggregated['Height'] = df.groupby(group_by)['Height'].first().values
                return df_aggregated
            # 处理数据
            # --- 新特征工程：Bag of Materials + 总数量 + 物料种类数 ---
            pivot = df.pivot_table(index=group_by, columns='Material', values='Packed Quantity', aggfunc='sum', fill_value=0)
            pivot.reset_index(inplace=True)
            # 新增总数量特征
            pivot['Total_Packed_Quantity'] = pivot.drop(columns=[group_by]).sum(axis=1)
            # 新增物料种类数特征
            pivot['Material_Type_Count'] = (pivot.drop(columns=[group_by]) > 0).sum(axis=1)
            # 合并目标变量和尺寸
            target = df.groupby(group_by)['Packaging Materials'].first().reset_index()
            dims = df.groupby(group_by)[['Length', 'Width', 'Height']].first().reset_index()
            hu_df = pd.merge(pivot, target, on=group_by)
            hu_df = pd.merge(hu_df, dims, on=group_by)
            hu_count = len(hu_df)
            logs_list.append(f"Total training samples (unique {group_by}): {hu_count}")
            # 记录训练集最大数量
            max_packed_quantity = 0
            if 'Packed Quantity' in df.columns:
                max_packed_quantity = df['Packed Quantity'].max()
            # 分类目标
            y_class = hu_df['Packaging Materials']
            label_encoder = LabelEncoder()
            y_class_enc = label_encoder.fit_transform(y_class)
            X_class = hu_df.drop(columns=[group_by, 'Packaging Materials', 'Length', 'Width', 'Height'], errors='ignore')
            # 分类模型
            X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X_class, y_class_enc, test_size=1-train_ratio, random_state=random_state)
            clf = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                min_samples_split=min_samples_split,
                min_samples_leaf=min_samples_leaf,
                max_features=max_features,
                bootstrap=bootstrap,
                class_weight='balanced')
            clf.fit(X_train_c, y_train_c)
            y_pred_c = clf.predict(X_test_c)
            acc = accuracy_score(y_test_c, y_pred_c)
            logs_list.append(f"Classification accuracy: {acc:.4f}")
            logs_list.append(str(classification_report(y_test_c, y_pred_c)))
            # 数值回归（长宽高）
            y_reg = hu_df[['Length', 'Width', 'Height']]
            X_reg = X_class.copy()
            X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_reg, y_reg, test_size=1-train_ratio, random_state=random_state)
            reg = MultiOutputRegressor(RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                min_samples_split=min_samples_split,
                min_samples_leaf=min_samples_leaf,
                max_features=max_features,
                bootstrap=bootstrap))
            reg.fit(X_train_r, y_train_r)
            y_pred_r = reg.predict(X_test_r)
            dim_metrics = {}
            for i, col in enumerate(y_reg.columns):
                rmse = np.sqrt(mean_squared_error(y_test_r.iloc[:, i], y_pred_r[:, i]))
                mae = mean_absolute_error(y_test_r.iloc[:, i], y_pred_r[:, i])
                r2 = r2_score(y_test_r.iloc[:, i], y_pred_r[:, i])
                dim_metrics[col] = {'RMSE': rmse, 'MAE': mae, 'R2': r2}
            logs_list.append(f"Regression (L/W/H) Mean R²: {np.mean([m['R2'] for m in dim_metrics.values()]):.4f}")
            # 保存模型（回退为原随机ID命名，修复model_pipeline未定义问题）
            model_pipeline = {
                'classification': clf,
                'regression': reg,
                'preprocessor': {'feature_columns': X_class.columns.tolist()},
                'label_encoder': label_encoder,
                'metadata': {'group_by': group_by, 'features': features, 'agg': agg, 'model_type': 'classification+regression', 'max_packed_quantity': int(max_packed_quantity)}
            }
            now_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            model_id = f"PACK_RF_{now_str}"
            save_dir = 'models'
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f'{model_id}.pkl')
            logs_list.append(f"Saving model to: {save_path}")
            try:
                with open(save_path, 'wb') as f:
                    pickle.dump(model_pipeline, f)
                logs_list.append(f"Model saved to: {save_path}")
            except Exception as save_err:
                logs_list.append(f"Model save failed: {save_err}")
            logs = '\n'.join(logs_list)
            results = {'model_id': model_id, 'save_path': save_path}
        except Exception as e:
            logs = f"Training failed: {str(e)}"
            results = ''
    # 页面渲染时可传递所有字段名供选择
    all_columns = []
    if datasets:
        try:
            sample_df = pd.read_csv(os.path.join(csv_path, datasets[0]))
            all_columns = list(sample_df.columns)
        except Exception:
            all_columns = []
    return render_template('training.html', datasets=datasets, logs=logs, results=results, all_columns=all_columns)
