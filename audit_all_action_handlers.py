import os
import re
import json

PAGES_DIR = r"c:\Users\amare\Documents\backend\frontend\src\app\pages"

def scan_handlers():
    findings = []

    for root, dirs, files in os.walk(PAGES_DIR):
        for file in files:
            if file.endswith(".ts") and not file.endswith(".spec.ts"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PAGES_DIR)

                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Find all methods ending with Dialog / afterClosed / Save / Create / Delete / Edit / Submit
                methods = re.findall(r"([a-zA-Z0-9_]+\s*\([^)]*\)\s*:\s*void\s*\{[^}]+\})", content, re.DOTALL)
                
                # Check for dialog afterClosed calls
                after_closed_blocks = re.findall(r"(afterClosed\(\)\.subscribe\(result\s*=>\s*\{[^}]+\}\);)", content, re.DOTALL)
                
                for block in after_closed_blocks:
                    has_service_call = "Service." in block or "service." in block or "Service)" in content
                    calls = re.findall(r"(this\.[a-zA-Z0-9_]+Service\.[a-zA-Z0-9_]+)", block)
                    local_update_only = ("dataSource" in block or "allVendors" in block) and len(calls) == 0
                    
                    findings.append({
                        "file": rel_path,
                        "snippet": block[:120].replace("\n", " "),
                        "calls": calls,
                        "has_service_call": len(calls) > 0,
                        "local_update_only": local_update_only
                    })

    print(f"Total afterClosed() action handlers analyzed: {len(findings)}")
    return findings

if __name__ == "__main__":
    results = scan_handlers()
    print(json.dumps(results, indent=2))
