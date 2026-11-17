/**
 * script.js
 * Frontend JavaScript for Credit Default Risk Management System.
 * Simple, clean functions to connect to FastAPI backend endpoints.
 */

// Global state variables
let currentBaselineCustomer = null;
let costChartInstance = null;
let allAlertsList = [];

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  fetchStats();
  loadRecentCustomers();
  loadCostComparison();
});

// 1. Tab Navigation
function switchTab(tabId) {
  // Update button active state
  document.querySelectorAll(".nav-btn").forEach(btn => btn.classList.remove("active"));
  const clickedBtn = Array.from(document.querySelectorAll(".nav-btn")).find(b =>
    b.getAttribute("onclick") && b.getAttribute("onclick").includes(tabId)
  );
  if (clickedBtn) clickedBtn.classList.add("active");

  // Show selected tab content
  document.querySelectorAll(".tab-content").forEach(tab => tab.classList.remove("active"));
  const targetTab = document.getElementById(`tab-${tabId}`);
  if (targetTab) targetTab.classList.add("active");

  // Load data for specific tab
  if (tabId === "dashboard") {
    fetchStats();
    loadRecentCustomers();
  } else if (tabId === "records") {
    loadCustomerRecords();
  } else if (tabId === "alerts") {
    loadAlerts();
  } else if (tabId === "whitelist") {
    loadWhitelist();
  } else if (tabId === "cost") {
    loadCostComparison();
  }
}

// 2. Dashboard Statistics
async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("cardTotal").innerText = data.total_customers || 0;
    document.getElementById("cardLow").innerText = data.low_risk || 0;
    document.getElementById("cardModerate").innerText = data.moderate_risk || 0;
    document.getElementById("cardHigh").innerText = data.high_risk || 0;
    document.getElementById("cardReviewed").innerText = data.reviewed_customers || 0;

    // Update alerts badge
    const alertRes = await fetch("/api/alerts");
    if (alertRes.ok) {
      const alerts = await alertRes.json();
      allAlertsList = alerts;
      const pendingCount = alerts.filter(a => a.alert_status === "Pending").length;
      const badge = document.getElementById("alertsBadge");
      if (badge) badge.innerText = pendingCount;
    }
  } catch (err) {
    console.error("Error fetching dashboard statistics:", err);
  }
}

// 3. Load Recent Records on Dashboard
async function loadRecentCustomers() {
  try {
    const res = await fetch("/api/customers");
    if (!res.ok) return;
    const records = await res.json();
    const tbody = document.getElementById("dashboardRecentBody");

    if (!records || records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center">No customer records saved yet.</td></tr>`;
      return;
    }

    const recent = records.slice(0, 5);
    tbody.innerHTML = recent.map(c => `
      <tr>
        <td><strong>${c.customer_id}</strong></td>
        <td>${c.probability}%</td>
        <td>${getRiskBadge(c.risk_category)}</td>
        <td>${getReviewBadge(c.review_status)}</td>
        <td>
          <a class="btn btn-outline btn-sm" href="/api/reports/download/${c.customer_id}" target="_blank">PDF Report</a>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading recent customers:", err);
  }
}

// 4. Quick Sample Buttons
function loadSample(type) {
  if (type === "high") {
    document.getElementById("customerId").value = "CUST-" + Math.floor(1000 + Math.random() * 9000);
    document.getElementById("limitBal").value = 20000;
    document.getElementById("sex").value = 2;
    document.getElementById("education").value = 2;
    document.getElementById("marriage").value = 1;
    document.getElementById("age").value = 24;
    document.getElementById("pay1").value = 2;
    document.getElementById("pay2").value = 2;
    document.getElementById("pay3").value = -1;
    document.getElementById("pay4").value = -1;
    document.getElementById("pay5").value = -2;
    document.getElementById("pay6").value = -2;
    document.getElementById("bill1").value = 3913;
    document.getElementById("bill2").value = 3102;
    document.getElementById("bill3").value = 689;
    document.getElementById("payAmt1").value = 0;
    document.getElementById("payAmt2").value = 689;
    document.getElementById("payAmt3").value = 0;
    document.getElementById("customThreshold").value = 0.41;
  } else {
    document.getElementById("customerId").value = "CUST-" + Math.floor(1000 + Math.random() * 9000);
    document.getElementById("limitBal").value = 250000;
    document.getElementById("sex").value = 1;
    document.getElementById("education").value = 1;
    document.getElementById("marriage").value = 2;
    document.getElementById("age").value = 35;
    document.getElementById("pay1").value = -1;
    document.getElementById("pay2").value = -1;
    document.getElementById("pay3").value = -1;
    document.getElementById("pay4").value = 0;
    document.getElementById("pay5").value = 0;
    document.getElementById("pay6").value = 0;
    document.getElementById("bill1").value = 8500;
    document.getElementById("bill2").value = 7200;
    document.getElementById("bill3").value = 6100;
    document.getElementById("payAmt1").value = 8500;
    document.getElementById("payAmt2").value = 7200;
    document.getElementById("payAmt3").value = 6100;
    document.getElementById("customThreshold").value = 0.41;
  }
}

function resetForm() {
  document.getElementById("predictForm").reset();
  document.getElementById("resultBadge").innerText = "Awaiting Input";
  document.getElementById("resultBadge").className = "badge";
  document.getElementById("resultDetails").innerHTML = `
    <div class="placeholder-text">Click <strong>"Predict Customer Risk"</strong> to compute the Machine Learning assessment.</div>
  `;
  document.getElementById("explainContent").innerHTML = `
    <p class="placeholder-text">Feature explanations will appear here after evaluation.</p>
  `;
  document.getElementById("whatIfResult").style.display = "none";
}

// 5. Predict Customer Risk Form Submit
async function handlePredict(event) {
  event.preventDefault();

  const customerId = document.getElementById("customerId").value.trim();
  const limitBal = parseFloat(document.getElementById("limitBal").value);
  const sex = parseInt(document.getElementById("sex").value);
  const education = parseInt(document.getElementById("education").value);
  const marriage = parseInt(document.getElementById("marriage").value);
  const age = parseInt(document.getElementById("age").value);
  const pay1 = parseInt(document.getElementById("pay1").value);
  const pay2 = parseInt(document.getElementById("pay2").value);
  const pay3 = parseInt(document.getElementById("pay3").value);
  const pay4 = parseInt(document.getElementById("pay4").value);
  const pay5 = parseInt(document.getElementById("pay5").value);
  const pay6 = parseInt(document.getElementById("pay6").value);
  const bill1 = parseFloat(document.getElementById("bill1").value);
  const bill2 = parseFloat(document.getElementById("bill2").value);
  const bill3 = parseFloat(document.getElementById("bill3").value);
  const payAmt1 = parseFloat(document.getElementById("payAmt1").value);
  const payAmt2 = parseFloat(document.getElementById("payAmt2").value);
  const payAmt3 = parseFloat(document.getElementById("payAmt3").value);
  const customThreshold = parseFloat(document.getElementById("customThreshold").value);

  const payload = {
    customer_id: customerId,
    LIMIT_BAL: limitBal,
    SEX: sex,
    EDUCATION: education,
    MARRIAGE: marriage,
    AGE: age,
    PAY_1: pay1,
    PAY_2: pay2,
    PAY_3: pay3,
    PAY_4: pay4,
    PAY_5: pay5,
    PAY_6: pay6,
    BILL_AMT1: bill1,
    BILL_AMT2: bill2,
    BILL_AMT3: bill3,
    BILL_AMT4: 0,
    BILL_AMT5: 0,
    BILL_AMT6: 0,
    PAY_AMT1: payAmt1,
    PAY_AMT2: payAmt2,
    PAY_AMT3: payAmt3,
    PAY_AMT4: 0,
    PAY_AMT5: 0,
    PAY_AMT6: 0,
    custom_threshold: isNaN(customThreshold) ? 0.41 : customThreshold
  };

  currentBaselineCustomer = { ...payload };

  const btn = document.getElementById("btnPredict");
  btn.innerText = "Evaluating...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      alert("Error calculating prediction. Please verify inputs.");
      return;
    }

    const data = await res.json();
    renderPredictionOutput(data);
    fetchStats();
  } catch (err) {
    console.error("Prediction error:", err);
    alert("Connection error while requesting prediction.");
  } finally {
    btn.innerText = "Predict Customer Risk";
    btn.disabled = false;
  }
}

// Render Prediction Result and Explanations
function renderPredictionOutput(data) {
  // Update header badge
  const badge = document.getElementById("resultBadge");
  badge.innerText = data.risk_category;
  badge.className = `badge ${getRiskBadgeClass(data.risk_category)}`;

  // Populate details
  const details = document.getElementById("resultDetails");
  details.innerHTML = `
    <div class="result-card-inner">
      <div class="result-metric-row">
        <span class="result-metric-label">Customer ID:</span>
        <span class="result-metric-val">${data.customer_id}</span>
      </div>
      <div class="result-metric-row">
        <span class="result-metric-label">Default Probability:</span>
        <span class="result-metric-val" style="color: ${getRiskColor(data.risk_category)}">${data.probability}%</span>
      </div>
      <div class="result-metric-row">
        <span class="result-metric-label">Binary Prediction:</span>
        <span class="result-metric-val">
          <span class="badge ${data.prediction === 'Default' ? 'badge-default' : 'badge-nodefault'}">${data.prediction}</span>
        </span>
      </div>
      <div class="result-metric-row">
        <span class="result-metric-label">Risk Category:</span>
        <span class="result-metric-val">${getRiskBadge(data.risk_category)}</span>
      </div>
      <div class="result-metric-row">
        <span class="result-metric-label">Decision Threshold Applied:</span>
        <span class="result-metric-val">${data.decision_threshold}</span>
      </div>

      <div class="form-actions" style="margin-top: 12px;">
        <a class="btn btn-navy btn-sm" href="/api/reports/download/${data.customer_id}" target="_blank">Download PDF Report</a>
        ${data.risk_category === "High Risk" ? `
          <button class="btn btn-outline btn-sm" onclick="openWhitelistModal('${data.customer_id}')">Add to Whitelist</button>
        ` : ''}
      </div>
    </div>
  `;

  // Render Explainable AI (SHAP)
  const explainDiv = document.getElementById("explainContent");
  if (data.top_reasons && data.top_reasons.length > 0) {
    explainDiv.innerHTML = `
      <ul class="reasons-list">
        ${data.top_reasons.map(r => `<li>${r}</li>`).join("")}
      </ul>
      <div class="info-box" style="margin-top: 10px;">
        <small><strong>Explainable AI Insight:</strong> Factors marked (+) increased the predicted default probability. Factors marked (-) protected the customer score.</small>
      </div>
    `;
  } else {
    explainDiv.innerHTML = `<p class="placeholder-text">No significant risk factors detected.</p>`;
  }

  // Pre-fill What-If simulator inputs
  document.getElementById("simPay1").value = document.getElementById("pay1").value;
  document.getElementById("simPayAmt1").value = document.getElementById("payAmt1").value;
}

// 6. What-If Simulator
async function runWhatIf() {
  if (!currentBaselineCustomer) {
    alert("Please run a baseline customer prediction first before simulating scenarios.");
    return;
  }

  const simPay1 = parseInt(document.getElementById("simPay1").value);
  const simPayAmt1 = parseFloat(document.getElementById("simPayAmt1").value) || 0;

  const modified = { ...currentBaselineCustomer };
  modified.PAY_1 = simPay1;
  modified.PAY_AMT1 = simPayAmt1;

  try {
    const res = await fetch("/api/whatif", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        original: currentBaselineCustomer,
        modified: modified,
        custom_threshold: currentBaselineCustomer.custom_threshold
      })
    });

    if (!res.ok) return;
    const diff = await res.json();
    renderWhatIfResult(diff);
  } catch (err) {
    console.error("What-If simulation error:", err);
  }
}

function renderWhatIfResult(data) {
  const container = document.getElementById("whatIfResult");
  container.style.display = "block";

  const diff = data.probability_difference;
  const diffColor = diff < 0 ? "var(--green-risk)" : diff > 0 ? "var(--red-risk)" : "var(--navy-primary)";
  const sign = diff > 0 ? "+" : "";

  container.innerHTML = `
    <h4 style="color: var(--navy-primary); font-size: 14px; margin-bottom: 6px;">Scenario Comparison Output:</h4>
    <p style="font-size: 13px; font-weight: 600; color: ${diffColor}; margin-bottom: 10px;">${data.change_summary} (${sign}${diff}%)</p>

    <div class="comparison-grid">
      <div class="comparison-col">
        <h5>Original Baseline</h5>
        <div class="comparison-prob" style="color: ${getRiskColor(data.original.risk_category)}">${data.original.probability}%</div>
        <div>${getRiskBadge(data.original.risk_category)}</div>
        <small style="color: var(--text-muted); display:block; margin-top: 4px;">Pred: ${data.original.prediction}</small>
      </div>

      <div class="comparison-col" style="border: 2px dashed ${diffColor}">
        <h5>Simulated Scenario</h5>
        <div class="comparison-prob" style="color: ${getRiskColor(data.scenario.risk_category)}">${data.scenario.probability}%</div>
        <div>${getRiskBadge(data.scenario.risk_category)}</div>
        <small style="color: var(--text-muted); display:block; margin-top: 4px;">Pred: ${data.scenario.prediction}</small>
      </div>
    </div>
    <div class="info-box" style="margin-top: 10px;">
      <small><strong>Note:</strong> What-If simulations are hypothetical tests and do not alter the saved customer record.</small>
    </div>
  `;
}

function resetWhatIf() {
  if (currentBaselineCustomer) {
    document.getElementById("simPay1").value = currentBaselineCustomer.PAY_1;
    document.getElementById("simPayAmt1").value = currentBaselineCustomer.PAY_AMT1;
  }
  document.getElementById("whatIfResult").style.display = "none";
}

// 7. Customer Records Table
async function loadCustomerRecords() {
  const search = document.getElementById("recordSearch").value.trim();
  const risk = document.getElementById("riskFilter").value;

  try {
    const url = `/api/customers?search=${encodeURIComponent(search)}&risk=${encodeURIComponent(risk)}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const records = await res.json();

    const tbody = document.getElementById("customerTableBody");
    if (!records || records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center">No matching records found.</td></tr>`;
      return;
    }

    tbody.innerHTML = records.map(c => `
      <tr>
        <td><strong>${c.customer_id}</strong></td>
        <td>${c.probability}%</td>
        <td><span class="badge ${c.prediction === 'Default' ? 'badge-default' : 'badge-nodefault'}">${c.prediction}</span></td>
        <td>${getRiskBadge(c.risk_category)}</td>
        <td>${getReviewBadge(c.review_status)}</td>
        <td>
          <div style="display:flex; gap: 6px;">
            <a class="btn btn-outline btn-sm" href="/api/reports/download/${c.customer_id}" target="_blank">PDF</a>
            ${c.review_status === "Not Reviewed" ? `
              <button class="btn btn-outline btn-sm" onclick="markReviewed('${c.customer_id}')">Review</button>
            ` : ''}
            ${c.risk_category === "High Risk" && c.review_status !== "Whitelisted" ? `
              <button class="btn btn-outline btn-sm" onclick="openWhitelistModal('${c.customer_id}')">Whitelist</button>
            ` : ''}
            <button class="btn btn-secondary btn-sm" onclick="deleteCustomer('${c.customer_id}')">Delete</button>
          </div>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading records:", err);
  }
}

function filterRecords() {
  loadCustomerRecords();
}

async function markReviewed(customerId) {
  try {
    await fetch(`/api/customers/${customerId}/reviewed`, { method: "POST" });
    loadCustomerRecords();
    fetchStats();
  } catch (err) {
    console.error("Error marking reviewed:", err);
  }
}

async function deleteCustomer(customerId) {
  if (!confirm(`Are you sure you want to delete customer ${customerId}?`)) return;
  try {
    await fetch(`/api/customers/${customerId}`, { method: "DELETE" });
    loadCustomerRecords();
    fetchStats();
  } catch (err) {
    console.error("Error deleting customer:", err);
  }
}

// 8. Whitelist Management
async function loadWhitelist() {
  try {
    const res = await fetch("/api/whitelist");
    if (!res.ok) return;
    const list = await res.json();
    const tbody = document.getElementById("whitelistTableBody");

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center">No whitelisted customers.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(item => `
      <tr>
        <td><strong>${item.customer_id}</strong></td>
        <td>${getRiskBadge(item.risk_category)}</td>
        <td>${item.probability}%</td>
        <td>
          <strong>${item.reason}</strong>
          ${item.notes ? `<br><small style="color:var(--text-muted)">${item.notes}</small>` : ''}
        </td>
        <td>${item.added_at}</td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="removeFromWhitelist('${item.customer_id}')">Remove</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading whitelist:", err);
  }
}

function openWhitelistModal(customerId) {
  document.getElementById("wlCustomerId").value = customerId;
  document.getElementById("wlNotes").value = "";
  document.getElementById("whitelistModal").classList.add("active");
}

async function handleAddToWhitelist(event) {
  event.preventDefault();
  const customerId = document.getElementById("wlCustomerId").value;
  const reason = document.getElementById("wlReason").value;
  const notes = document.getElementById("wlNotes").value;

  try {
    const res = await fetch("/api/whitelist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_id: customerId, reason: reason, notes: notes })
    });

    if (res.ok) {
      closeModal("whitelistModal");
      alert(`Customer ${customerId} added to whitelist.\n\nReminder: Whitelist means the customer has been reviewed. It does not mean the customer has no risk.`);
      loadWhitelist();
      loadCustomerRecords();
      fetchStats();
    }
  } catch (err) {
    console.error("Error adding to whitelist:", err);
  }
}

async function removeFromWhitelist(customerId) {
  if (!confirm(`Remove ${customerId} from whitelist?`)) return;
  try {
    await fetch(`/api/whitelist/${customerId}`, { method: "DELETE" });
    loadWhitelist();
    loadCustomerRecords();
    fetchStats();
  } catch (err) {
    console.error("Error removing from whitelist:", err);
  }
}

// 9. Customer Alerts
async function loadAlerts() {
  try {
    const res = await fetch("/api/alerts");
    if (!res.ok) return;
    const alerts = await res.json();
    allAlertsList = alerts;
    const tbody = document.getElementById("alertsTableBody");

    if (!alerts || alerts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center">No active risk alerts.</td></tr>`;
      return;
    }

    tbody.innerHTML = alerts.map(a => `
      <tr>
        <td><strong>${a.customer_id}</strong></td>
        <td>${getRiskBadge(a.risk_level)}</td>
        <td>${a.probability}%</td>
        <td>${a.alert_date}</td>
        <td><span class="badge ${a.alert_status === 'Pending' ? 'badge-high' : a.alert_status === 'Sent' ? 'badge-moderate' : 'badge-low'}">${a.alert_status}</span></td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-outline btn-sm" onclick="openAlertModal(${a.id})">Preview Message</button>
            ${a.alert_status === 'Pending' ? `
              <button class="btn btn-navy btn-sm" onclick="quickAlertStatus(${a.id}, 'Sent')">Send (Demo)</button>
            ` : ''}
            ${a.alert_status !== 'Resolved' ? `
              <button class="btn btn-secondary btn-sm" onclick="quickAlertStatus(${a.id}, 'Resolved')">Resolve</button>
            ` : ''}
          </div>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Error loading alerts:", err);
  }
}

function openAlertModal(alertId) {
  const alertItem = allAlertsList.find(a => a.id === alertId);
  if (!alertItem) return;

  document.getElementById("alertModalId").value = alertItem.id;
  document.getElementById("alertModalCustomer").value = alertItem.customer_id;
  document.getElementById("alertModalMessage").value = alertItem.message;
  document.getElementById("alertModalStatus").value = alertItem.alert_status;

  document.getElementById("alertModal").classList.add("active");
}

async function handleSaveAlert(event) {
  event.preventDefault();
  const alertId = document.getElementById("alertModalId").value;
  const status = document.getElementById("alertModalStatus").value;
  const message = document.getElementById("alertModalMessage").value;

  try {
    await fetch(`/api/alerts/${alertId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: status, message: message })
    });
    closeModal("alertModal");
    loadAlerts();
    fetchStats();
  } catch (err) {
    console.error("Error saving alert:", err);
  }
}

async function markAlertStatus(status) {
  const alertId = document.getElementById("alertModalId").value;
  const message = document.getElementById("alertModalMessage").value;
  try {
    await fetch(`/api/alerts/${alertId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: status, message: message })
    });
    closeModal("alertModal");
    loadAlerts();
    fetchStats();
  } catch (err) {
    console.error("Error updating alert status:", err);
  }
}

async function quickAlertStatus(alertId, status) {
  try {
    await fetch(`/api/alerts/${alertId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: status })
    });
    loadAlerts();
    fetchStats();
  } catch (err) {
    console.error("Error updating alert status:", err);
  }
}

// 10. Cost Comparison & Chart.js
async function loadCostComparison() {
  try {
    const res = await fetch("/api/cost-comparison");
    if (!res.ok) return;
    const data = await res.json();

    const records = data.threshold_records || [];
    const optThresh = data.optimal_threshold;

    // Render highlight text
    const highlight = document.getElementById("optimalThreshHighlight");
    if (highlight) {
      highlight.innerHTML = `
        <strong>Optimal Decision Threshold: ${optThresh}</strong><br>
        At threshold ${optThresh}, the bank balances missed defaults against false alert review costs, achieving the lowest overall financial cost.
      `;
    }

    // Render table
    const tbody = document.getElementById("costTableBody");
    if (tbody) {
      tbody.innerHTML = records.map(r => `
        <tr style="${r.threshold === optThresh ? 'background-color: #f0fff4; font-weight: bold;' : ''}">
          <td>${r.threshold} ${r.threshold === optThresh ? '(Optimal)' : ''}</td>
          <td>${r.tp}</td>
          <td>${r.fp}</td>
          <td>${r.tn}</td>
          <td>${r.fn}</td>
          <td>$${r.cost.toLocaleString()}</td>
        </tr>
      `).join("");
    }

    // Render Chart.js
    renderCostChart(records, optThresh);
  } catch (err) {
    console.error("Error loading cost comparison:", err);
  }
}

function renderCostChart(records, optimalThreshold) {
  const ctx = document.getElementById("costChart");
  if (!ctx) return;

  const labels = records.map(r => r.threshold.toFixed(2));
  const costs = records.map(r => r.cost);

  if (costChartInstance) {
    costChartInstance.destroy();
  }

  costChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Total Business Cost ($)",
        data: costs,
        borderColor: "#1a2a40",
        backgroundColor: "rgba(26, 42, 64, 0.08)",
        borderWidth: 2.5,
        fill: true,
        tension: 0.3,
        pointBackgroundColor: records.map(r => r.threshold === optimalThreshold ? "#27ae60" : "#1a2a40"),
        pointRadius: records.map(r => r.threshold === optimalThreshold ? 7 : 3)
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` Total Cost: $${context.raw.toLocaleString()}`;
            }
          }
        }
      },
      scales: {
        x: {
          title: { display: true, text: "Decision Threshold", font: { weight: "bold" } }
        },
        y: {
          title: { display: true, text: "Total Business Cost ($)", font: { weight: "bold" } },
          ticks: {
            callback: function(value) {
              return "$" + (value / 1000) + "k";
            }
          }
        }
      }
    }
  });
}

// Helpers
function closeModal(modalId) {
  document.getElementById(modalId).classList.remove("active");
}

function getRiskBadge(category) {
  if (category === "Low Risk") return `<span class="badge badge-low">Low Risk</span>`;
  if (category === "Moderate Risk") return `<span class="badge badge-moderate">Moderate Risk</span>`;
  return `<span class="badge badge-high">High Risk</span>`;
}

function getRiskBadgeClass(category) {
  if (category === "Low Risk") return "green";
  if (category === "Moderate Risk") return "orange";
  return "red";
}

function getRiskColor(category) {
  if (category === "Low Risk") return "var(--green-risk)";
  if (category === "Moderate Risk") return "var(--orange-risk)";
  return "var(--red-risk)";
}

function getReviewBadge(status) {
  if (status === "Whitelisted") return `<span class="badge badge-moderate">Whitelisted</span>`;
  if (status === "Reviewed") return `<span class="badge badge-low">Reviewed</span>`;
  return `<span class="badge" style="background:#edf2f7; color:#4a5568;">Not Reviewed</span>`;
}

