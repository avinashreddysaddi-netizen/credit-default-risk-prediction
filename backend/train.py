"""
train.py
ML Model Training script for Credit Default Risk Prediction.
Implements the exact Tuned & Regularized XGBoost Pipeline from Untitled1.ipynb:
1. 5 Custom Engineered Features:
   - DELAY_COUNT: Count of months with payment delays (> 0)
   - MAX_DELAY: Maximum payment delay code across 6 months
   - AVG_BILL_AMT: 6-month average bill statement amount
   - AVG_PAY_AMT: 6-month average payment amount
   - PAYMENT_BILL_RATIO: Ratio of payments to bills
2. Preprocessor Pipeline:
   - Numerical: SimpleImputer(median) + StandardScaler()
   - Categorical: SimpleImputer(most_frequent) + OneHotEncoder(ignore)
3. XGBClassifier with regularized parameters:
   - scale_pos_weight: 4 (penalizes missed defaults)
   - n_estimators: 600, max_depth: 5, learning_rate: 0.01
   - subsample: 0.9, colsample_bytree: 0.8
   - reg_alpha: 1, reg_lambda: 1
4. Evaluates test set and saves final_credit_default_model.pkl & threshold (0.41).
"""

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)


def train_xgboost_pipeline():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "dataset.xls")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    print("Step 1: Loading dataset from:", data_path)
    df = pd.read_excel(data_path, header=1)

    target_col = "default payment next month"
    y = df[target_col].copy()
    X = df.drop(columns=["ID", target_col]).copy()

    # Step 2: Feature Engineering (from Untitled1.ipynb)
    print("Step 2: Computing 5 custom financial features...")
    pay_cols = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
    bill_cols = ["BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6"]
    pay_amt_cols = ["PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"]

    X["DELAY_COUNT"] = (X[pay_cols] > 0).sum(axis=1)
    X["MAX_DELAY"] = X[pay_cols].clip(lower=0).max(axis=1)
    X["AVG_BILL_AMT"] = X[bill_cols].mean(axis=1)
    X["AVG_PAY_AMT"] = X[pay_amt_cols].mean(axis=1)
    X["PAYMENT_BILL_RATIO"] = X["AVG_PAY_AMT"] / X["AVG_BILL_AMT"].replace(0, np.nan)

    # Step 3: Train-Test Split (80% train, 20% test, stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Dataset split: Train = {X_train.shape[0]} records, Test = {X_test.shape[0]} records")

    # Step 4: Build Preprocessing Pipeline
    categorical_cols = ["SEX", "EDUCATION", "MARRIAGE"]
    numerical_cols = [c for c in X_train.columns if c not in categorical_cols]

    numerical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("num", numerical_pipeline, numerical_cols),
        ("cat", categorical_pipeline, categorical_cols)
    ])

    # Step 5: Define Tuned & Regularized XGBoost Pipeline
    classifier = XGBClassifier(
        random_state=42,
        eval_metric="logloss",
        n_jobs=-1,
        scale_pos_weight=4,
        n_estimators=600,
        max_depth=5,
        learning_rate=0.01,
        subsample=0.9,
        colsample_bytree=0.8,
        reg_alpha=1,
        reg_lambda=1
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", classifier)
    ])

    # Step 6: Train the Model
    print("Step 6: Fitting Regularized XGBoost Pipeline...")
    pipeline.fit(X_train, y_train)

    # Step 7: Evaluate on Test Data
    probs = pipeline.predict_proba(X_test)[:, 1]
    optimal_threshold = 0.41  # Optimal threshold determined in Untitled1.ipynb

    preds = (probs >= optimal_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()

    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)
    roc_auc = roc_auc_score(y_test, probs)
    pr_auc = average_precision_score(y_test, probs)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS ON 6,000 TEST CUSTOMERS:")
    print("=" * 60)
    print(f"ROC-AUC Score:          {roc_auc:.4f}")
    print(f"PR-AUC (Avg Precision): {pr_auc:.4f}")
    print(f"Default Recall:         {rec * 100:.2f}% ({tp} out of {tp + fn} caught)")
    print(f"Precision:              {prec * 100:.2f}%")
    print(f"Overall Accuracy:       {acc * 100:.2f}%")
    print(f"F1-Score:               {f1:.4f}")
    print(f"Decision Threshold:     {optimal_threshold}")

    # Step 8: Save Model Artifacts
    model_path1 = os.path.join(models_dir, "final_credit_default_model.pkl")
    model_path2 = os.path.join(models_dir, "model.pkl")
    thresh_path = os.path.join(models_dir, "final_credit_default_threshold.pkl")
    prep_path = os.path.join(models_dir, "model_metadata.pkl")

    joblib.dump(pipeline, model_path1)
    joblib.dump(pipeline, model_path2)
    joblib.dump(optimal_threshold, thresh_path)

    # Build cost table
    cost_fn = 500.0
    cost_fp = 50.0
    threshold_records = []
    for t in np.arange(0.10, 0.95, 0.05):
        p_t = (probs >= t).astype(int)
        tn_t, fp_t, fn_t, tp_t = confusion_matrix(y_test, p_t).ravel()
        cost = (fn_t * cost_fn) + (fp_t * cost_fp)
        threshold_records.append({
            "threshold": round(float(t), 2),
            "tp": int(tp_t), "fp": int(fp_t), "tn": int(tn_t), "fn": int(fn_t),
            "cost": float(cost)
        })

    meta = {
        "model_name": "Tuned Regularized XGBoost",
        "optimal_threshold": optimal_threshold,
        "cost_fn": cost_fn,
        "cost_fp": cost_fp,
        "threshold_records": threshold_records,
        "raw_features": ['LIMIT_BAL', 'SEX', 'EDUCATION', 'MARRIAGE', 'AGE', 'PAY_0', 'PAY_2', 'PAY_3', 'PAY_4', 'PAY_5', 'PAY_6', 'BILL_AMT1', 'BILL_AMT2', 'BILL_AMT3', 'BILL_AMT4', 'BILL_AMT5', 'BILL_AMT6', 'PAY_AMT1', 'PAY_AMT2', 'PAY_AMT3', 'PAY_AMT4', 'PAY_AMT5', 'PAY_AMT6'],
        "feature_names": list(X.columns)
    }
    joblib.dump(meta, prep_path)

    print(f"\nArtifacts saved successfully to {models_dir}!")


if __name__ == "__main__":
    train_xgboost_pipeline()
