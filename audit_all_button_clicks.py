import os
import re
import json

PAGES_DIR = r"c:\Users\amare\Documents\backend\frontend\src\app\pages"

def audit_all_components():
    component_audit = {}
    
    for root, dirs, files in os.walk(PAGES_DIR):
        for file in files:
            if file.endswith(".ts") and not file.endswith(".spec.ts"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PAGES_DIR)

                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    ts_code = f.read()

                html_path = full_path.replace(".ts", ".html")
                html_code = ""
                if os.path.exists(html_path):
                    with open(html_path, "r", encoding="utf-8", errors="ignore") as hf:
                        html_code = hf.read()

                # Extract method names called by (click) in HTML
                clicks = re.findall(r"\(click\)=\"([a-zA-Z0-9_]+)\([^)]*\)\"", html_code)
                
                # Check for API calls inside component
                services = re.findall(r"([a-zA-Z0-9_]+Service)", ts_code)
                api_calls = re.findall(r"(this\.[a-zA-Z0-9_]+Service\.[a-zA-Z0-9_]+)", ts_code)

                # Check if component opens a dialog
                dialog_open = "dialog.open" in ts_code or "MatDialog" in ts_code

                component_audit[rel_path] = {
                    "clicks": list(set(clicks)),
                    "services": list(set(services)),
                    "api_calls": list(set(api_calls)),
                    "opens_dialog": dialog_open,
                    "ts_lines": len(ts_code.splitlines())
                }

    return component_audit

if __name__ == "__main__":
    report = audit_all_components()
    print(json.dumps(report, indent=2))
