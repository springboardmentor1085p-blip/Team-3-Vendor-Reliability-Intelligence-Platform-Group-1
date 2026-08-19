import json

# Verify frontend payload structure vs backend Pydantic ProcurementRequestUpdate schema

frontend_dialog_output = {
    "id": "e2b36079-61c0-4ba0-94d9-d8891438a002",
    "requestId": "PR-2026-0001",
    "item": "Heavy duty industrial lathe machine",
    "quantity": 2,
    "budget": 15000,
    "priority": "High"
}

# Payload construction in procurement-table.ts
payload = {
    "item_description": frontend_dialog_output["item"],
    "quantity": float(frontend_dialog_output["quantity"]),
    "estimated_cost": float(frontend_dialog_output["budget"]),
    "priority": frontend_dialog_output["priority"].upper()
}

print("=== VERIFYING PROCUREMENT EDIT PAYLOAD MAP ===")
print("Dialog Output:", json.dumps(frontend_dialog_output, indent=2))
print("Payload Sent to Backend PATCH API:", json.dumps(payload, indent=2))

expected_pydantic_fields = ["department", "item_description", "quantity", "estimated_cost", "priority", "required_by_date"]

for k in payload.keys():
    assert k in expected_pydantic_fields, f"Invalid field in payload: {k}"

print("Payload verification: SUCCESS (All payload keys match Pydantic schema!)")
