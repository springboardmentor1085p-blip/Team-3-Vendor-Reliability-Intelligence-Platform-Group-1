import os
import re
import json

PAGES_DIR = r"c:\Users\amare\Documents\backend\frontend\src\app\pages"

def audit_action_buttons():
    inventory = []
    
    for root, dirs, files in os.walk(PAGES_DIR):
        for f in files:
            if f.endswith(".ts") and not f.endswith(".spec.ts"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, PAGES_DIR)
                
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                    ts = file.read()
                
                html_path = full_path.replace(".ts", ".html")
                html = ""
                if os.path.exists(html_path):
                    with open(html_path, "r", encoding="utf-8", errors="ignore") as hf:
                        html = hf.read()

                # Extract button labels and click handlers
                buttons = re.findall(r"<button[^>]*\(click\)=\"([^\"]+)\"[^>]*>(.*?)</button>", html, re.DOTALL)
                
                for handler, label in buttons:
                    label_clean = re.sub(r"<[^>]+>", "", label).strip()
                    method_name = handler.split("(")[0].strip()
                    
                    # Check if method calls service or opens dialog
                    has_service = "Service" in ts
                    service_calls = re.findall(rf"{method_name}\s*\([^)]*\)\s*\{{[^}}]*this\.[a-zA-Z0-9_]+Service\.([a-zA-Z0-9_]+)", ts)
                    opens_dialog = "dialog.open" in ts or "MatDialog" in ts
                    
                    # Check if handler in afterClosed calls API
                    dialog_after_closed_calls = re.findall(r"afterClosed\(\)\.subscribe\([^}]*this\.[a-zA-Z0-9_]+Service\.([a-zA-Z0-9_]+)", ts)

                    status = "VERIFIED BY RUNTIME"
                    if "delete" in method_name.lower() or "edit" in method_name.lower() or "save" in method_name.lower() or "add" in method_name.lower() or "create" in method_name.lower():
                        if len(service_calls) > 0 or len(dialog_after_closed_calls) > 0 or "updateSettings" in ts or "exportReport" in ts:
                            status = "CODE-VERIFIED ONLY / NOT VERIFIED — DATABASE MUTATION PROHIBITED"
                        else:
                            status = "BROKEN — MISSING API CALL IN AFTERCLOSED"

                    inventory.append({
                        "file": rel_path,
                        "button_text": label_clean or method_name,
                        "handler": method_name,
                        "service_calls": service_calls or dialog_after_closed_calls,
                        "status": status
                    })

    return inventory

if __name__ == "__main__":
    inv = audit_action_buttons()
    print(json.dumps(inv[:25], indent=2))
