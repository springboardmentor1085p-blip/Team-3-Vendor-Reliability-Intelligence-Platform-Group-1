import json
import urllib.request

def main():
    url = "http://127.0.0.1:8000/openapi.json"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    spec = json.loads(resp.read().decode())

    paths = spec.get("paths", {})
    routes = []

    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]:
                summary = operation.get("summary", "")
                security = operation.get("security", [])
                auth_req = "YES" if security or path not in ["/", "/health", "/docs", "/redoc", "/openapi.json", "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password"] else "NO"
                
                routes.append({
                    "method": method.upper(),
                    "path": f"/api/v1{path}" if not path.startswith("/api/v1") and path not in ["/", "/health", "/docs", "/redoc", "/openapi.json"] else path,
                    "summary": summary,
                    "auth_required": auth_req
                })

    # Sort routes by path and method
    routes.sort(key=lambda r: (r["path"], r["method"]))

    print(f"=== EXACT OPENAPI ROUTE COUNT: {len(routes)} ===")
    print(json.dumps(routes, indent=2))

if __name__ == "__main__":
    main()
