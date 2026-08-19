import urllib.request
import urllib.error
import json
import os

def check_http(url):
    try:
        resp = urllib.request.urlopen(url)
        return resp.getcode(), resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return None, str(e)

def main():
    print("=== PHASE 1 — CURRENT APPLICATION STATE VERIFICATION ===")
    
    # 1. Backend check
    b_st, b_data = check_http("http://127.0.0.1:8000/health")
    print(f"Backend Status: {b_st} | Data: {b_data[:60]}...")
    assert b_st == 200, "Backend service unavailable"

    # 2. Frontend check
    f_st, _ = check_http("http://localhost:4200/")
    print(f"Frontend Status: {f_st}")
    assert f_st == 200, "Frontend service unavailable"

    # 3. Source code fix verification
    table_path = r"c:\Users\amare\Documents\backend\frontend\src\app\pages\procurement-management\components\procurement-table\procurement-table.ts"
    service_path = r"c:\Users\amare\Documents\backend\frontend\src\app\services\procurement.service.ts"

    with open(table_path, "r", encoding="utf-8") as f:
        t_code = f.read()
    with open(service_path, "r", encoding="utf-8") as f:
        s_code = f.read()

    assert "updateRequest" in s_code, "procurement.service.ts updateRequest missing!"
    assert s_code.count("updateRequest") == 1, "Duplicate updateRequest in procurement.service.ts!"
    assert "this.procurementService.updateRequest" in t_code, "procurement-table.ts updateRequest missing!"
    print("Procurement Edit Save fix verification: PASSED (Fix intact, zero duplicates)")

if __name__ == "__main__":
    main()
