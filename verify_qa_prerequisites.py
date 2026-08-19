import urllib.request
import json

OPENAPI_URL = "http://127.0.0.1:8000/openapi.json"

MUTATION_ENDPOINTS = [
    ("POST", "/api/v1/vendors"),
    ("PUT", "/api/v1/vendors/{vendor_id}"),
    ("DELETE", "/api/v1/vendors/{vendor_id}"),
    ("POST", "/api/v1/procurement/requests"),
    ("PATCH", "/api/v1/procurement/requests/{request_id}"),
    ("POST", "/api/v1/procurement/requests/{request_id}/approve"),
    ("POST", "/api/v1/procurement/requests/{request_id}/reject"),
    ("POST", "/api/v1/procurement/requests/{request_id}/cancel"),
    ("POST", "/api/v1/procurement/purchase-orders"),
    ("POST", "/api/v1/procurement/purchase-orders/{po_id}/approve"),
    ("POST", "/api/v1/procurement/purchase-orders/{po_id}/deliver"),
    ("POST", "/api/v1/procurement/purchase-orders/{po_id}/complete"),
    ("POST", "/api/v1/contracts"),
    ("POST", "/api/v1/communications"),
    ("PUT", "/api/v1/settings")
]

def main():
    print("=== VERIFYING QA TEST PREREQUISITES FOR ALL 15 MUTATION ENDPOINTS ===")
    
    req = urllib.request.urlopen(OPENAPI_URL)
    oa = json.loads(req.read().decode("utf-8"))
    paths = oa.get("paths", {})

    missing = []
    for method, full_path in MUTATION_ENDPOINTS:
        path_obj = paths.get(full_path)
        if not path_obj or method.lower() not in path_obj:
            missing.append((method, full_path))
        else:
            op = path_obj[method.lower()]
            print(f"  [OK] {method:<6} {full_path:<55} -> Summary: {op.get('summary')}")

    assert len(missing) == 0, f"Missing OpenAPI endpoints: {missing}"
    print("\nAll 15 Mutation Endpoints VERIFIED intact in FastAPI OpenAPI specification!")
    print("QA Test Readiness Status: READY FOR TEST DATABASE")

if __name__ == "__main__":
    main()
