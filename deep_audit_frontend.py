import os
import re
import json

PAGES_DIR = r"c:\Users\amare\Documents\backend\frontend\src\app\pages"

def inspect_page(page_name):
    page_path = os.path.join(PAGES_DIR, page_name)
    components = []
    
    for root, dirs, files in os.walk(page_path):
        for file in files:
            if file.endswith(".ts") and not file.endswith(".spec.ts"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PAGES_DIR)
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    ts_content = f.read()

                html_path = full_path.replace(".ts", ".html")
                html_content = ""
                if os.path.exists(html_path):
                    with open(html_path, "r", encoding="utf-8", errors="ignore") as hf:
                        html_content = hf.read()

                # Detect data binding & hardcoded arrays
                hardcoded_matches = re.findall(r"(\b[a-zA-Z0-9_]+\s*:\s*[^=\n]+=\s*\[\s*\{[^\]]+\}\s*\];)", ts_content, re.DOTALL)
                services_used = re.findall(r"([a-zA-Z0-9_]+Service)", ts_content)
                api_calls = re.findall(r"(this\.[a-zA-Z0-9_]+Service\.[a-zA-Z0-9_]+)", ts_content)
                button_handlers = re.findall(r"\(click\)=\"([a-zA-Z0-9_]+)\(\)\"", html_content)
                form_controls = re.findall(r"formControlName=\"([a-zA-Z0-9_]+)\"", html_content)

                components.append({
                    "file": rel_path,
                    "services": list(set(services_used)),
                    "api_calls": list(set(api_calls)),
                    "button_handlers": button_handlers,
                    "form_controls": form_controls,
                    "hardcoded_count": len(hardcoded_matches),
                    "hardcoded_snippets": [m[:100] + "..." for m in hardcoded_matches]
                })

    return components

if __name__ == "__main__":
    pages = [d for d in os.listdir(PAGES_DIR) if os.path.isdir(os.path.join(PAGES_DIR, d))]
    full_report = {}
    for p in pages:
        full_report[p] = inspect_page(p)

    print(json.dumps(full_report, indent=2))
