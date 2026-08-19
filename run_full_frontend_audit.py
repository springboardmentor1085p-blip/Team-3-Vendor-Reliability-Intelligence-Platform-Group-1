import os
import re
import json

APP_DIR = r"c:\Users\amare\Documents\backend\frontend\src\app"

def audit():
    total_pages = set()
    components = []
    services = []
    models = []
    
    total_buttons = 0
    total_forms = 0
    total_charts = 0
    total_tables = 0
    
    real_data_components = 0
    hardcoded_components = 0
    fallback_components = 0
    broken_integrations = []
    
    for root, dirs, files in os.walk(APP_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, APP_DIR)
            
            if f.endswith(".service.ts"):
                services.append(rel_path)
            elif f.endswith(".ts") and not f.endswith(".spec.ts"):
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                    code = file.read()
                
                if "pages" in rel_path:
                    parts = rel_path.split(os.sep)
                    if len(parts) > 1:
                        total_pages.add(parts[1])
                
                is_component = "@Component" in code
                if is_component:
                    components.append(rel_path)
                    
                    # Counts
                    if "Chart" in code or "chart" in code:
                        total_charts += 1
                    if "Table" in code or "table" in code or "MatTable" in code:
                        total_tables += 1
                    if "FormGroup" in code or "fb.group" in code:
                        total_forms += 1
                    if "Service" in code and ("subscribe" in code or "inject(" in code):
                        real_data_components += 1
                    else:
                        hardcoded_components += 1

            if f.endswith(".html"):
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                    html = file.read()
                button_matches = len(re.findall(r"<button|\bmat-button\b|\bmat-raised-button\b|\bmat-icon-button\b", html))
                total_buttons += button_matches

    report_data = {
        "pages_count": len(total_pages),
        "pages": sorted(list(total_pages)),
        "components_count": len(components),
        "services_count": len(services),
        "total_buttons": total_buttons,
        "total_forms": total_forms,
        "total_charts": total_charts,
        "total_tables": total_tables,
        "real_data_components": real_data_components,
        "hardcoded_components": hardcoded_components
    }
    
    print(json.dumps(report_data, indent=2))
    return report_data

if __name__ == "__main__":
    audit()
