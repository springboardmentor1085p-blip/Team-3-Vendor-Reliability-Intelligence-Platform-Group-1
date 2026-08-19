import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:8000/api/v1"

def test_api(method, path, token=None, body=None):
    url = f"{BASE}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    else:
        data = None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        raw = resp.read().decode("utf-8")
        try:
            return resp.status, json.loads(raw)
        except Exception:
            return resp.status, raw
    except urllib.error.HTTPError as e:
        body_str = e.read().decode("utf-8", errors="ignore")
        try:
            return e.code, json.loads(body_str)
        except Exception:
            return e.code, body_str

def run_network_audit():
    print("=== RUNTIME NETWORK AUDIT (FRONTEND API INTEGRATION) ===")
    
    # 1. Login
    st, data = test_api("POST", "/auth/login", body={"username": "testuser", "password": "password123"})
    print(f"POST /auth/login -> Status {st}")
    assert st == 200, f"Login failed with status {st}"
    token = data["access_token"]

    # 2. Test Endpoints consumed by Angular Services
    endpoints = [
        ("AnalyticsService.getDashboardMetrics", "GET", "/analytics/dashboard"),
        ("AnalyticsService.getProcurementAnalytics", "GET", "/analytics/procurement"),
        ("AnalyticsService.getVendorAnalytics", "GET", "/analytics/vendors"),
        ("VendorService.getVendors", "GET", "/vendors"),
        ("ProcurementService.getRequests", "GET", "/procurement/requests"),
        ("PurchaseOrderService.getPurchaseOrders", "GET", "/procurement/purchase-orders"),
        ("ContractService.getContracts", "GET", "/contracts"),
        ("CommunicationService.getMessages", "GET", "/communications"),
        ("VendorPerformanceService.getRankings", "GET", "/vendor-performance/rankings"),
        ("ReportService.getReportHistory", "GET", "/reports/history"),
        ("SettingsService.getSettings", "GET", "/settings"),
    ]

    for service_method, method, path in endpoints:
        st, res_data = test_api(method, path, token=token)
        count = len(res_data) if isinstance(res_data, list) else (len(res_data.get("items", [])) if isinstance(res_data, dict) and "items" in res_data else "dict")
        print(f"{service_method:<45} | {method} {path:<30} -> Status {st} | Count/Data: {count}")

if __name__ == "__main__":
    run_network_audit()
