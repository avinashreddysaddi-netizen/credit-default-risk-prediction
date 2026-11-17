# AI-Based Credit Default Risk Prediction and Management System

A beginner-friendly Machine Learning and Web Application project that predicts whether a credit card customer will fail to make their next payment.

Designed with clean Python code, simple explanations, and an intuitive dashboard so that anyone—from a 10th-class student to a college viva examiner—can easily understand every step.

---

## 📁 1. Project Folder Structure

```text
credit_default_project/
│
├── data/
│   ├── dataset.xls                     # Actual UCI Credit Card Default Dataset (30,000 customers)
│   └── default of credit card clients.xls
│
├── notebooks/
│   └── model_training.ipynb            # Complete, step-by-step Jupyter Notebook with explanations
│
├── models/
│   ├── final_credit_default_model.pkl  # Upgraded Tuned Regularized XGBoost Pipeline (Best Model)
│   ├── final_credit_default_threshold.pkl # Optimal threshold (0.41)
│   ├── model.pkl                       # Active model used by backend
│   └── preprocessing.pkl               # Pipeline metadata, feature names & cost records
│
├── backend/
│   ├── main.py                         # FastAPI web server and REST API endpoints
│   ├── model.py                        # Model loading, predictions, SHAP explanations & What-If
│   ├── database.py                     # SQLite database helper (customers, whitelist, alerts)
│   ├── report_generator.py             # Professional PDF report generation using ReportLab
│   └── train.py                        # Standalone script to retrain the ML model from CLI
│
├── frontend/
│   ├── index.html                      # Clean, responsive web interface
│   ├── style.css                       # White background, navy blue headings, risk badges
│   └── script.js                       # Interactive charts, What-If simulator, and API calls
│
├── reports/
│   ├── figures/                        # Generated EDA charts (default rates, age, credit limits)
│   └── Risk_Report_*.pdf               # Generated customer assessment PDF reports
│
├── requirements.txt                    # Python library dependencies
└── README.md                           # Documentation, run guide, and viva preparation
```

---

## 🚀 2. How to Run the Project in VS Code on Windows

Follow these exact steps:

### Step 1: Open VS Code
1. Launch **Visual Studio Code**.
2. Click **File** &gt; **Open Folder...**
3. Select the folder: `c:\Users\avina\Desktop\anti100\credit_default_project`

### Step 2: Open the Integrated Terminal
- Press **``Ctrl + ` ``** (Ctrl + Backtick) or go to the top menu: **Terminal** &gt; **New Terminal**.
- In the terminal, confirm your current directory is inside `credit_default_project`. If not, run:
  ```powershell
  cd c:\Users\avina\Desktop\anti100\credit_default_project
  ```

### Step 3: Install Required Libraries (One-Time Setup)
Run this command in the terminal:
```powershell
pip install -r requirements.txt
```
*(If you have multiple Python versions installed, run `python -m pip install -r requirements.txt`)*

### Step 4: (Optional) Retrain the Machine Learning Model
The trained model files (`model.pkl` and `preprocessing.pkl`) are already included in the `models/` folder. If you wish to retrain from scratch:
```powershell
cd backend
python train.py
cd ..
```

### Step 5: Start the Web Application
Run the FastAPI backend server using Uvicorn:
```powershell
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Step 6: Open the Website in Your Browser
Open your browser (Google Chrome, Microsoft Edge, etc.) and visit:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

You will see the complete **Credit Default Risk Management System**!

---

## 🌟 3. Website Features & Where to Click

| Feature | Where to Click | Description |
| :--- | :--- | :--- |
| **1. Executive Dashboard** | Click the **"Dashboard"** tab | Displays 5 live summary metric cards (Total Customers, Low Risk, Moderate Risk, High Risk, Customers Reviewed) and recent high-risk accounts. |
| **2. Predict Risk** | Click the **"Predict & What-If"** tab | Enter financial details or click **"Load High Risk Sample"** / **"Load Low Risk Sample"**, then click **"Predict Customer Risk"**. |
| **3. Explain Why (SHAP)** | Right column under **"Explain Why"** | Shows the exact positive (+) and negative (-) factors influencing the prediction in plain English. |
| **4. What-If Simulator** | Bottom right on the Predict page | Change hypothetical payment delay or payment amount, click **"Run What-If Scenario"** to view side-by-side risk changes. |
| **5. Smart Risk Badges** | Everywhere across the app | 🟢 **Low Risk** (< 25%), 🟠 **Moderate Risk** (25% - 50%), 🔴 **High Risk** (≥ 50%). |
| **6. Customer Records** | Click the **"Customer Records"** tab | Live search by Customer ID and filter by Risk level. Click **"Review"** to mark reviewed, or **"PDF"** to generate reports. |
| **7. Customer Whitelist** | Click the **"Whitelist"** tab | Review high-risk accounts and add documented managerial exceptions with notes. Includes prominent governance disclaimer. |
| **8. Customer Alerts** | Click the **"Customer Alerts"** tab | Manage automated payment reminders for high-risk accounts. Click **"Preview Message"**, edit reminder text, mark **"Sent"** or **"Resolved"**. |
| **9. Cost Comparison** | Click the **"Cost Analysis"** tab | Interactive Chart.js graph of Decision Threshold vs Business Cost ($), comparing missed defaults ($500) vs false alarms ($50). |
| **10. Download PDF** | Click **"Download PDF Report"** | Instantly downloads a formatted PDF report with executive summary, financial profile, and SHAP drivers. |

---

## 🧠 4. Machine Learning Workflow Explained

### Step 1: Load the Dataset
- We read `dataset.xls` (30,000 customers, 25 columns).
- Target column: `default.payment.next.month`
  - `0` = Customer paid on time (23,364 customers / 77.88%).
  - `1` = Customer defaulted (6,636 customers / 22.12%).
- Verified 0 null values and 0 duplicate rows.

### Step 2: Clean the Data
- Removed `ID` because a serial number does not represent financial behavior.
- Cleaned unknown codes in `EDUCATION` (values 0, 4, 5, 6 mapped to 4 = Others) and `MARRIAGE` (0 mapped to 3 = Others).
- Standardized column names (`PAY_0` to `PAY_1`).

### Step 3: Train-Test Split
- **80% Training (24,000 records)**: Used to train the ML models.
- **20% Testing (6,000 records)**: Held out to evaluate model performance on unseen data.
- Used **Stratified Splitting** (`stratify=y`) so both sets preserve the exact 77.88% / 22.12% class balance.

### Step 4: Class Imbalance Handling
- In credit card datasets, default is a minority event (22%).
- If a naive model simply predicts "No Default" for everyone, it achieves 77.9% accuracy but catches **zero** defaulters!
- We compared **SMOTE** (Synthetic Minority Over-sampling Technique) and **Class Weighting** (`class_weight='balanced'`).

### Step 5: 5-Model Comparison

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** | 80.83% | 69.03% | 24.19% | 0.3583 | 0.7079 |
| **Decision Tree** | 81.67% | 65.66% | 35.87% | 0.4639 | 0.7447 |
| **Random Forest (Selected)** | **81.72%** | **66.67%** | **34.66%** | **0.4561** | **0.7718** |
| **Support Vector Machine (SVM)** | 80.73% | 68.31% | 24.04% | 0.3556 | 0.7045 |
| **XGBoost** | 81.88% | 66.81% | 35.95% | 0.4674 | 0.7787 |

### Step 6: Decision Threshold Optimization
- The model outputs a probability between `0.0` and `1.0`.
- Standard threshold is `0.50`. But in banking, a **False Negative** (missing a customer who defaults) costs much more than a **False Positive** (reaching out to a customer who would pay).
- **Assumed Business Costs**:
  - Missed Default (False Negative) = **$500**
  - False Alert Outreach (False Positive) = **$50**
- Testing thresholds from 0.10 to 0.90 reveals:
  - At **0.50**: 867 defaults are missed &rarr; **Total Cost: $445,000**
  - At **0.20**: Missed defaults cut in half &rarr; **Total Cost: $287,350**
  - At **0.10**: Almost all defaults detected &rarr; **Total Cost: $218,000**
- The system allows testing custom operational thresholds live on the website!

---

## 🎓 5. College Viva / Interview Questions & Answers

**Q1: Why did you not rely on Accuracy alone to select the best model?**  
*Answer:* Accuracy is misleading on imbalanced datasets. Because 78% of customers do not default, a dumb model predicting "No Default" for everyone would score 78% accuracy while missing 100% of defaults. We used **Recall**, **PR-AUC**, and **F1-Score** to ensure defaulters are reliably detected.

**Q2: What is the purpose of the Decision Threshold?**  
*Answer:* The ML model outputs a continuous probability (e.g. 0.32). The threshold is the cutoff point above which we classify the customer as "Default". Lowering the threshold catches more defaults early at the cost of a few extra phone calls or reviews.

**Q3: What does SHAP do in this project?**  
*Answer:* SHAP (SHapley Additive exPlanations) explains the contribution of each individual feature to a customer's specific risk score. For example, it proves mathematically that a 2-month repayment delay in September added +24.9% to the customer's default probability.

**Q4: What is the difference between Whitelist and Risk Prediction?**  
*Answer:* Adding a customer to the Whitelist records human review and business approval (e.g., collateral or payroll standing). Crucially, it does **not** alter or erase the machine learning statistical default probability, maintaining complete audit transparency.

