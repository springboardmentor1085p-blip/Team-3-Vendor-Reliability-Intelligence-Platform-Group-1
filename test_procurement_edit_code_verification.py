import os

def check_file(path, search_str):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert search_str in content, f"Missing {search_str} in {path}"
    print(f"Verified {search_str[:40]}... in {os.path.basename(path)}")

def main():
    print("=== TESTING PROCUREMENT EDIT CODE VERIFICATION ===")
    
    # 1. Check procurement.service.ts
    service_path = r"c:\Users\amare\Documents\backend\frontend\src\app\services\procurement.service.ts"
    check_file(service_path, "updateRequest(requestId: string, data: any)")
    check_file(service_path, "http.patch<any>(`${this.apiUrl}/procurement/requests/${requestId}`, data)")
    
    # 2. Check procurement-table.ts
    table_path = r"c:\Users\amare\Documents\backend\frontend\src\app\pages\procurement-management\components\procurement-table\procurement-table.ts"
    check_file(table_path, "id: request.request_id")
    check_file(table_path, "this.procurementService.updateRequest(targetId, payload)")
    check_file(table_path, "this.dataSource[index] = {")
    
    print("\nCode verification: ALL CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
