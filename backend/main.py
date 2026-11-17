"""
main.py
FastAPI Backend for AI-Based Credit Default Risk Prediction and Management System.
Connects the Machine Learning model, SQLite database, and frontend UI.
"""

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# Local module imports
from database import (
    init_db,
    get_dashboard_stats,
    save_customer_prediction,
    get_all_customers,
    get_customer_by_id,
    add_to_whitelist,
    get_whitelist,
    remove_from_whitelist,
    mark_customer_reviewed,
    get_all_alerts,
    update_alert,
    delete_customer_record
)
from model import predict_customer, simulate_what_if, get_cost_comparison_data
from report_generator import generate_pdf_report

# Initialize database tables on server startup
init_db()

app = FastAPI(
    title="AI Credit Default Risk Management System",
    description="Beginner-friendly Credit Card Default Prediction with FastAPI and ML",
    version="1.0.0"
)

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


# Pydantic Schemas for Request Validation
class PredictRequest(BaseModel):
    customer_id: str = Field(..., example="CUST-2001")
    LIMIT_BAL: float = Field(20000, example=20000)
    SEX: int = Field(2, example=2)
    EDUCATION: int = Field(2, example=2)
    MARRIAGE: int = Field(1, example=1)
    AGE: int = Field(24, example=24)
    PAY_1: int = Field(2, example=2)
    PAY_2: int = Field(2, example=2)
    PAY_3: int = Field(-1, example=-1)
    PAY_4: int = Field(-1, example=-1)
    PAY_5: int = Field(-2, example=-2)
    PAY_6: int = Field(-2, example=-2)
    BILL_AMT1: float = Field(3913, example=3913)
    BILL_AMT2: float = Field(3102, example=3102)
    BILL_AMT3: float = Field(689, example=689)
    BILL_AMT4: float = Field(0, example=0)
    BILL_AMT5: float = Field(0, example=0)
    BILL_AMT6: float = Field(0, example=0)
    PAY_AMT1: float = Field(0, example=0)
    PAY_AMT2: float = Field(689, example=689)
    PAY_AMT3: float = Field(0, example=0)
    PAY_AMT4: float = Field(0, example=0)
    PAY_AMT5: float = Field(0, example=0)
    PAY_AMT6: float = Field(0, example=0)
    custom_threshold: Optional[float] = None


class WhatIfRequest(BaseModel):
    original: Dict[str, Any]
    modified: Dict[str, Any]
    custom_threshold: Optional[float] = None


class WhitelistRequest(BaseModel):
    customer_id: str
    reason: str
    notes: Optional[str] = ""


class AlertUpdateRequest(BaseModel):
    status: str
    message: Optional[str] = None


# 1. API: Dashboard Metrics
@app.get("/api/stats")
def get_stats():
    """Returns 5 summary metrics for the dashboard cards."""
    return get_dashboard_stats()


# 2. API: Predict Customer Risk
@app.post("/api/predict")
def predict_risk(data: PredictRequest):
    """Predicts risk for a customer, explains it, and saves to database."""
    inputs = data.model_dump()
    customer_id = inputs.pop("customer_id")
    threshold = inputs.pop("custom_threshold", None)

    # Run ML prediction and explainability
    pred_result = predict_customer(inputs, threshold)

    # Save to database
    save_record = {
        "customer_id": customer_id,
        "probability": pred_result["probability"],
        "prediction": pred_result["prediction"],
        "risk_category": pred_result["risk_category"],
        "limit_bal": data.LIMIT_BAL,
        "age": data.AGE,
        "pay_1": data.PAY_1,
        "bill_amt1": data.BILL_AMT1,
        "pay_amt1": data.PAY_AMT1,
        "top_reasons": pred_result["top_reasons"]
    }
    save_customer_prediction(save_record)

    return {
        "customer_id": customer_id,
        **pred_result
    }


# 3. API: What-If Simulator
@app.post("/api/whatif")
def what_if_simulation(data: WhatIfRequest):
    """Compares baseline vs modified scenario using ML model."""
    result = simulate_what_if(data.original, data.modified, data.custom_threshold)
    return result


# 4. API: Customer Records List
@app.get("/api/customers")
def list_customers(
    search: Optional[str] = Query(None),
    risk: Optional[str] = Query("All")
):
    """Returns all saved customer records."""
    return get_all_customers(search=search or "", risk_filter=risk)


@app.get("/api/customers/{customer_id}")
def get_single_customer(customer_id: str):
    """Returns details for a single customer."""
    cust = get_customer_by_id(customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    return cust


@app.post("/api/customers/{customer_id}/reviewed")
def set_customer_reviewed(customer_id: str):
    """Marks customer review status as Reviewed."""
    mark_customer_reviewed(customer_id)
    return {"status": "success", "message": f"Customer {customer_id} marked as Reviewed."}


@app.delete("/api/customers/{customer_id}")
def delete_customer(customer_id: str):
    """Deletes a customer record from database."""
    delete_customer_record(customer_id)
    return {"status": "success", "message": f"Customer {customer_id} deleted."}


# 5. API: Customer Whitelist
@app.get("/api/whitelist")
def list_whitelist():
    """Returns all whitelisted customers."""
    return get_whitelist()


@app.post("/api/whitelist")
def add_whitelist_entry(entry: WhitelistRequest):
    """Adds a customer to the whitelist with justification."""
    add_to_whitelist(entry.customer_id, entry.reason, entry.notes or "")
    return {
        "status": "success",
        "message": f"Customer {entry.customer_id} added to whitelist.",
        "disclaimer": "Whitelist means the customer has been reviewed. It does not mean the customer has no risk."
    }


@app.delete("/api/whitelist/{customer_id}")
def remove_whitelist_entry(customer_id: str):
    """Removes a customer from the whitelist."""
    remove_from_whitelist(customer_id)
    return {"status": "success", "message": f"Customer {customer_id} removed from whitelist."}


# 6. API: Customer Alerts
@app.get("/api/alerts")
def list_alerts():
    """Returns all risk alerts."""
    return get_all_alerts()


@app.put("/api/alerts/{alert_id}")
def update_alert_item(alert_id: int, update_data: AlertUpdateRequest):
    """Updates status or message for an alert."""
    update_alert(alert_id, update_data.status, update_data.message)
    return {"status": "success", "message": f"Alert {alert_id} updated."}


# 7. API: Cost Matrix & Threshold Comparison
@app.get("/api/cost-comparison")
def cost_comparison():
    """Returns thresholds, confusion matrix counts, and business costs."""
    return get_cost_comparison_data()


# 8. API: Download PDF Report
@app.get("/api/reports/download/{customer_id}")
def download_customer_report(customer_id: str):
    """Generates and serves a PDF report for a customer."""
    cust = get_customer_by_id(customer_id)
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    pdf_filename = f"Risk_Report_{customer_id}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    generate_pdf_report(cust, pdf_path)

    return FileResponse(
        path=pdf_path,
        filename=pdf_filename,
        media_type="application/pdf"
    )


# Serve Static Frontend Files (HTML, CSS, JS)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

