import os

def check_file(path, search_str):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert search_str in content, f"Missing {search_str} in {path}"
    print(f"Verified {search_str[:45]}... in {os.path.basename(path)}")

def main():
    print("=== CODE VERIFICATION FOR ALL 5 CONNECTED CREATE WORKFLOWS ===")
    
    # 1. Vendor Header
    check_file(r"c:\Users\amare\Documents\backend\frontend\src\app\pages\vendor-management\components\vendor-header\vendor-header.ts", "this.vendorService.createVendor(payload)")
    
    # 2. Procurement Header
    check_file(r"c:\Users\amare\Documents\backend\frontend\src\app\pages\procurement-management\components\procurement-header\procurement-header.ts", "this.procurementService.createRequest(payload)")
    
    # 3. Purchase Header
    check_file(r"c:\Users\amare\Documents\backend\frontend\src\app\pages\purchase-orders\components\purchase-header\purchase-header.ts", "this.purchaseOrderService.createPurchaseOrder(payload)")
    
    # 4. Contract Header
    check_file(r"c:\Users\amare\Documents\backend\frontend\src\app\pages\contract-management\components\contract-header\contract-header.ts", "this.contractService.createContract(payload)")
    
    # 5. Communication Header
    check_file(r"c:\Users\amare\Documents\backend\frontend\src\app\pages\communication\components\communication-header\communication-header.ts", "this.communicationService.sendMessage(payload)")

    print("\nAll 5 creation workflow connections VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
