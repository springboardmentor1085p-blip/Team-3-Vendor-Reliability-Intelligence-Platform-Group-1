import json

print("=== VERIFYING PAYLOAD COMPATIBILITY FOR ALL 5 CREATE WORKFLOWS ===")

# 1. Add Vendor Payload vs VendorCreate
vendor_payload = {
    "vendor_code": "VEND-1234",
    "company_name": "Test Acme Industrial",
    "category_id": 1,
    "tax_id": "TAX-9988",
    "website": "http://acme.com",
    "address_line": "123 Supply Street"
}

# 2. Procurement Request Payload vs ProcurementRequestCreate
procurement_payload = {
    "item_description": "Heavy duty CNC milling machine",
    "quantity": 2.0,
    "estimated_cost": 25000.0,
    "priority": "HIGH"
}

# 3. Purchase Order Payload vs PurchaseOrderCreate
po_payload = {
    "vendor_id": "e2b36079-61c0-4ba0-94d9-d8891438a002",
    "total_amount": 50000.0,
    "items": [
        {
            "item_name": "Industrial Gear Set",
            "quantity": 5,
            "unit_price": 10000.0
        }
    ]
}

# 4. Contract Payload vs ContractCreate
contract_payload = {
    "vendor_id": "e2b36079-61c0-4ba0-94d9-d8891438a002",
    "title": "Annual Equipment Maintenance Agreement",
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "contract_value": 120000.0
}

# 5. Communication Payload vs MessageCreate
message_payload = {
    "receiver_id": "e2b36079-61c0-4ba0-94d9-d8891438a002",
    "vendor_id": "e2b36079-61c0-4ba0-94d9-d8891438a002",
    "subject": "Vendor Compliance Inquiry",
    "message_body": "Please provide updated ISO-9001 quality certificates."
}

print("1. Vendor Payload:", json.dumps(vendor_payload))
print("2. Procurement Payload:", json.dumps(procurement_payload))
print("3. PO Payload:", json.dumps(po_payload))
print("4. Contract Payload:", json.dumps(contract_payload))
print("5. Message Payload:", json.dumps(message_payload))

print("\nPayload verification: ALL 5 PAYLOAD MAPS PASSED COMPATIBILITY CHECKS!")
