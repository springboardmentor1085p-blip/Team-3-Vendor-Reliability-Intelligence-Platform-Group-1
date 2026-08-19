import os
import re
import json

FRONTEND_PATH = r"c:\Users\amare\Documents\backend\frontend\src\app"

def audit_files():
    results = []
    
    for root, dirs, files in os.walk(FRONTEND_PATH):
        for file in files:
            if file.endswith(".ts") or file.endswith(".html"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, FRONTEND_PATH)
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Checks
                has_hardcoded_array = bool(re.search(r"=\s*\[\s*\{", content))
                has_mock_keyword = bool(re.search(r"(mock|dummy|sample|fake|placeholder)", content, re.IGNORECASE))
                has_http_client = "HttpClient" in content
                has_service = "Service" in content
                has_click_handler = "(click)=" in content or "onClick" in content
                has_chart = "chart" in content.lower() or "canvas" in content.lower()
                has_form = "FormGroup" in content or "formControlName" in content or "<form" in content

                results.append({
                    "path": rel_path,
                    "is_html": file.endswith(".html"),
                    "hardcoded_array": has_hardcoded_array,
                    "mock_keyword": has_mock_keyword,
                    "http_client": has_http_client,
                    "service": has_service,
                    "click_handler": has_click_handler,
                    "chart": has_chart,
                    "form": has_form,
                    "lines": len(content.splitlines())
                })
                
    print(f"Total frontend components/templates analyzed: {len(results)}")
    return results

if __name__ == "__main__":
    data = audit_files()
    print(json.dumps(data[:15], indent=2))
