"""
model.py
Upgraded Machine Learning inference module using the Tuned & Regularized XGBoost Pipeline
from Untitled1.ipynb (final_credit_default_model.pkl).
Includes automatic feature engineering (DELAY_COUNT, MAX_DELAY, AVG_BILL_AMT,
AVG_PAY_AMT, PAYMENT_BILL_RATIO), SHAP TreeExplainer, and What-If simulation.
"""

import os
import joblib
import numpy as np
import pandas as pd
import shap

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "final_credit_default_model.pkl")
THRESH_PATH = os.path.join(MODELS_DIR, "final_credit_default_threshold.pkl")
PREP_PATH = os.path.join(MODELS_DIR, "preprocessing.pkl")

# Cached objects
_pipeline = None
_meta = None
_explainer = None
_preprocessor = None
_classifier = None
_feature_names_out = None


def load_artifacts():
    """Loads the upgraded XGBoost Pipeline and SHAP explainer."""
    global _pipeline, _meta, _explainer, _preprocessor, _classifier, _feature_names_out

    if _pipeline is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

        _pipeline = joblib.load(MODEL_PATH)

        if os.path.exists(PREP_PATH):
            _meta = joblib.load(PREP_PATH)
        else:
            _meta = {}

        if os.path.exists(THRESH_PATH):
            _meta["optimal_threshold"] = float(joblib.load(THRESH_PATH))

        _preprocessor = _pipeline.named_steps.get("preprocessor")
        _classifier = _pipeline.named_steps.get("classifier")

        # TreeExplainer for the XGBoost classifier
        _explainer = shap.TreeExplainer(_classifier)
        _feature_names_out = _preprocessor.get_feature_names_out()

    return _pipeline, _meta, _explainer, _preprocessor, _classifier, _feature_names_out


def engineer_customer_features(input_dict):
    """
    Takes raw customer financial fields and computes the 5 engineered features
    from Untitled1.ipynb:
    1. DELAY_COUNT: Total number of delayed payment months (> 0)
    2. MAX_DELAY: Maximum delay month code
    3. AVG_BILL_AMT: Average bill statement amount
    4. AVG_PAY_AMT: Average monthly payment made
    5. PAYMENT_BILL_RATIO: Ratio of payments to bills
    """
    row = dict(input_dict)

    # Normalize PAY_1 vs PAY_0
    if "PAY_1" in row and "PAY_0" not in row:
        row["PAY_0"] = row["PAY_1"]
    elif "PAY_0" in row and "PAY_1" not in row:
        row["PAY_1"] = row["PAY_0"]

    df = pd.DataFrame([row])

    # 1 & 2: Repayment features
    pay_cols = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
    for c in pay_cols:
        if c not in df.columns:
            df[c] = 0

    df["DELAY_COUNT"] = (df[pay_cols] > 0).sum(axis=1)
    df["MAX_DELAY"] = df[pay_cols].clip(lower=0).max(axis=1)

    # 3: Bill amounts
    bill_cols = ["BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6"]
    for c in bill_cols:
        if c not in df.columns:
            df[c] = 0
    df["AVG_BILL_AMT"] = df[bill_cols].mean(axis=1)

    # 4: Payment amounts
    pay_amt_cols = ["PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"]
    for c in pay_amt_cols:
        if c not in df.columns:
            df[c] = 0
    df["AVG_PAY_AMT"] = df[pay_amt_cols].mean(axis=1)

    # 5: Payment to bill ratio
    df["PAYMENT_BILL_RATIO"] = (
    df["AVG_PAY_AMT"] /
    df["AVG_BILL_AMT"].replace(0, np.nan)
)
    # Expected column order by pipeline
    expected_cols = [
        "LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE",
        "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",
        "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
        "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
        "DELAY_COUNT", "MAX_DELAY", "AVG_BILL_AMT", "AVG_PAY_AMT", "PAYMENT_BILL_RATIO"
    ]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0

    return df[expected_cols]


def format_feature_explanation(feat_name, shap_val, raw_df):
    """
    Translates transformed feature names and SHAP impacts into simple English.
    """
    clean_name = feat_name.replace("num__", "").replace("cat__", "")
    direction = "increased default risk" if shap_val > 0 else "reduced default risk (protective)"

    name_map = {
        "PAY_0": "September repayment delay",
        "PAY_1": "September repayment delay",
        "PAY_2": "August repayment delay",
        "PAY_3": "July repayment delay",
        "PAY_4": "June repayment delay",
        "PAY_5": "May repayment delay",
        "PAY_6": "April repayment delay",
        "DELAY_COUNT": "Total count of delayed payment months",
        "MAX_DELAY": "Highest payment delay severity",
        "LIMIT_BAL": "Credit limit balance",
        "AGE": "Customer age",
        "BILL_AMT1": "Latest monthly bill amount",
        "AVG_BILL_AMT": "6-month average bill statement",
        "PAY_AMT1": "Latest monthly payment amount",
        "AVG_PAY_AMT": "6-month average payment amount",
        "PAYMENT_BILL_RATIO": "Payment-to-bill settlement ratio",
        "SEX_1": "Gender classification (Male)",
        "SEX_2": "Gender classification (Female)",
        "EDUCATION_1": "Education (Graduate School)",
        "EDUCATION_2": "Education (University)",
        "MARRIAGE_1": "Marital status (Married)",
        "MARRIAGE_2": "Marital status (Single)"
    }

    display_name = name_map.get(clean_name, clean_name)
    sign = "+" if shap_val > 0 else "-"
    pct = abs(shap_val) * 100

    return f"{display_name} {direction} (impact: {sign}{pct:.1f}%)"


def determine_risk_category(prob_pct, low_cut=25.0, high_cut=50.0):
    """Categorizes risk into Low (green), Moderate (orange), and High (red)."""
    if prob_pct < low_cut:
        return "Low Risk"
    elif prob_pct < high_cut:
        return "Moderate Risk"
    else:
        return "High Risk"


def predict_customer(input_dict, custom_threshold=None):
    """
    Runs the upgraded XGBoost Pipeline with automatic feature engineering.
    """
    pipeline, meta, explainer, preprocessor, classifier, feat_names_out = load_artifacts()

    # Optimal threshold from notebook: 0.41
    optimal_thresh = meta.get("optimal_threshold", 0.41)
    threshold = float(custom_threshold) if custom_threshold is not None else float(optimal_thresh)

    # 1. Engineer features
    df_features = engineer_customer_features(input_dict)

    # 2. Predict default probability
    probabilities = pipeline.predict_proba(df_features)[0]
    prob_default = float(probabilities[1])
    prob_pct = round(prob_default * 100, 2)

    # 3. Binary decision
    prediction = "Default" if prob_default >= threshold else "No Default"
    risk_category = determine_risk_category(prob_pct)

    # 4. Compute SHAP explanations
    X_trans = preprocessor.transform(df_features)

    shap_vals = explainer.shap_values(X_trans)

    shap_array = np.asarray(shap_vals)

    if shap_array.ndim == 3:
        vals = shap_array[0, :, 1]

    elif shap_array.ndim == 2:
        vals = shap_array[0]

    else:
        raise ValueError("Unexpected SHAP output shape")

    top_indices = np.argsort(np.abs(vals))[::-1][:5]
    top_reasons = []
    for idx in top_indices:
        fn = feat_names_out[idx]
        val = vals[idx]
        top_reasons.append(format_feature_explanation(fn, val, df_features))

    return {
        "probability": prob_pct,
        "raw_probability": round(prob_default, 4),
        "prediction": prediction,
        "risk_category": risk_category,
        "decision_threshold": threshold,
        "top_reasons": top_reasons,
        "model_used": "Tuned Regularized XGBoost Pipeline"
    }


def simulate_what_if(original_inputs, modified_inputs, custom_threshold=None):
    """
    Compares baseline vs modified inputs using the upgraded XGBoost model.
    """
    original_result = predict_customer(original_inputs, custom_threshold)
    scenario_result = predict_customer(modified_inputs, custom_threshold)

    prob_diff = round(scenario_result["probability"] - original_result["probability"], 2)

    if prob_diff < 0:
        change_summary = f"Risk reduced by {abs(prob_diff):.2f}%"
    elif prob_diff > 0:
        change_summary = f"Risk increased by {prob_diff:.2f}%"
    else:
        change_summary = "No change in risk probability"

    return {
        "original": original_result,
        "scenario": scenario_result,
        "probability_difference": prob_diff,
        "change_summary": change_summary
    }


def get_cost_comparison_data():
    """Returns threshold and cost matrix evaluation records."""
    _, meta, _, _, _, _ = load_artifacts()
    return {
        "optimal_threshold": meta.get("optimal_threshold", 0.41),
        "cost_fn": meta.get("cost_fn", 500.0),
        "cost_fp": meta.get("cost_fp", 50.0),
        "threshold_records": meta.get("threshold_records", []),
        "model_name": meta.get("model_name", "Tuned Regularized XGBoost")
    }
