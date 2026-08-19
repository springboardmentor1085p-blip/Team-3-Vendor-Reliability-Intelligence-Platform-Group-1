import os
import re
import json

PAGES_DIR = r"c:\Users\amare\Documents\backend\frontend\src\app\pages"

def scan_all_actions():
    action_items = []

    for root, dirs, files in os.walk(PAGES_DIR):
        for f in files:
            if f.endswith(".ts") and not f.endswith(".spec.ts"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, PAGES_DIR)

                with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                    ts_code = file.read()

                html_path = full_path.replace(".ts", ".html")
                html_code = ""
                if os.path.exists(html_path):
                    with open(html_path, "r", encoding="utf-8", errors="ignore") as hf:
                        html_code = hf.read()

                # Find all methods in TS
                methods = re.findall(r"([a-zA-Z0-9_]+)\s*\([^)]*\)\s*:\s*void\s*\{", ts_code)

                # Check methods called in HTML
                clicks = re.findall(r"\(click\)=\"([a-zA-Z0-9_]+)\([^)]*\)\"", html_code)
                menus = re.findall(r"\(click\)=\"([a-zA-Z0-9_]+)\([^)]*\)\"", html_code)

                for m in set(clicks + menus + methods):
                    if m in ["ngOnInit", "ngOnChanges", "mapVendor", "applyFilters", "formatAmount", "openDialog", "cancel"]:
                        continue

                    # Check what the method does
                    # Does it call a service method?
                    service_calls = re.findall(rf"{m}\s*\([^)]*\)[^{{]*\{{[^}}]*this\.[a-zA-Z0-9_]+Service\.([a-zA-Z0-9_]+)", ts_code, re.DOTALL)
                    
                    # Does it open a dialog?
                    opens_dialog = f"{m}" in ts_code and "dialog.open" in ts_code

                    action_items.append({
                        "file": rel_path,
                        "method": m,
                        "service_calls": service_calls,
                        "opens_dialog": opens_dialog
                    })

    return action_items

if __name__ == "__main__":
    items = scan_all_actions()
    print(json.dumps(items[:30], indent=2))
