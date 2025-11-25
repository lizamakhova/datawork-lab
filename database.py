import random

# Генератор тестовых данных
DEMO_DATABASE = {
    "processing_operations": [
        # PARTNER_A операции (60)
        *[{"processing_id": f"PA{i:03d}", "created_date": "2025-01-15", "finalized_date": "2025-01-15", 
           "amount": round(random.uniform(50, 500), 2), "currency": "EUR", "status": "success", 
           "commission_amount": None, "partner_contract_id": "PARTNER_A"} for i in range(1, 41)],
        
        *[{"processing_id": f"PA{i:03d}", "created_date": "2025-01-15", "finalized_date": "2025-01-15", 
           "amount": round(random.uniform(50, 500), 2), "currency": "EUR", "status": "failed", 
           "commission_amount": None, "partner_contract_id": "PARTNER_A"} for i in range(41, 51)],
        
        *[{"processing_id": f"PA{i:03d}", "created_date": "2025-01-15", "finalized_date": "2025-01-16", 
           "amount": round(random.uniform(50, 500), 2), "currency": "EUR", "status": "pending", 
           "commission_amount": None, "partner_contract_id": "PARTNER_A"} for i in range(51, 61)],
        
        # PARTNER_B операции (40)
        *[{"processing_id": f"PB{i:03d}", "created_date": "2025-01-15", "finalized_date": "2025-01-15", 
           "amount": round(random.uniform(100, 800), 2), "currency": "EUR", "status": "success", 
           "commission_amount": None, "partner_contract_id": "PARTNER_B"} for i in range(1, 31)],
        
        *[{"processing_id": f"PB{i:03d}", "created_date": "2025-01-15", "finalized_date": "2025-01-15", 
           "amount": round(random.uniform(100, 800), 2), "currency": "EUR", "status": "failed", 
           "commission_amount": None, "partner_contract_id": "PARTNER_B"} for i in range(31, 41)],
        
        # ПРОБЛЕМНЫЕ ОПЕРАЦИИ
        {"processing_id": "PA023", "created_date": "2025-01-15", "finalized_date": "2025-01-15", 
         "amount": 245.50, "currency": "EUR", "status": "success", "commission_amount": 5.41, "partner_contract_id": "PARTNER_A"},
        
        {"processing_id": "PA037", "created_date": "2025-01-15", "finalized_date": "2025-01-15", 
         "amount": 189.75, "currency": "EUR", "status": "success", "commission_amount": 4.30, "partner_contract_id": "PARTNER_A"},
    ],
    
    "operation_additional_data": [
        *[{"processing_id": f"PA{i:03d}", "additional_type": "partner_operation_id", "additional_value": f"PTR_A_{i:03d}"} for i in range(1, 61)],
        *[{"processing_id": f"PB{i:03d}", "additional_type": "partner_operation_id", "additional_value": f"PTR_B_{i:03d}"} for i in range(1, 41)],
    ],
    
    "partner_a_payments": [
        *[{"partner_id": f"PTR_A_{i:03d}", "processing_id": f"PA{i:03d}", "status": "COMPLETED", 
           "commission": None, "registry_id": "REG001"} for i in range(1, 41)],
        
        *[{"partner_id": f"PTR_A_{i:03d}", "processing_id": f"PA{i:03d}", "status": "DECLINED", 
           "commission": 0, "registry_id": "REG001"} for i in range(41, 51)],
           
        *[{"partner_id": f"PTR_A_{i:03d}", "processing_id": f"PA{i:03d}", "status": "IN_PROGRESS", 
           "commission": 0, "registry_id": "REG001"} for i in range(51, 61)],
        
        # РАСХОЖДЕНИЯ
        {"partner_id": "PTR_A_023", "processing_id": "PA023", "status": "DECLINED", "commission": 0, "registry_id": "REG001"},
        {"partner_id": "PTR_A_037", "processing_id": "PA037", "status": "COMPLETED", "commission": 3.20, "registry_id": "REG001"},
    ],
    
    "partner_b_payments": [
        *[{"partner_id": f"PTR_B_{i:03d}", "status": "SUCCESS", "commission": None, "registry_id": "REG_B_001"} for i in range(1, 26)],
        *[{"partner_id": f"PTR_B_{i:03d}", "status": "FAILED", "commission": 0, "registry_id": "REG_B_001"} for i in range(26, 31)],
        *[{"partner_id": f"PTR_B_{i:03d}", "status": "SUCCESS", "commission": None, "registry_id": "REG_B_002"} for i in range(16, 26)],
        *[{"partner_id": f"PTR_B_{i:03d}", "status": "FAILED", "commission": 0, "registry_id": "REG_B_002"} for i in range(31, 36)],
    ],
    
    "registry_statuses": [
        {"registry_id": "REG001", "registry_date": "2025-01-15", "partner_contract_id": "PARTNER_A", "is_excluded": 0},
        {"registry_id": "REG002", "registry_date": "2025-01-15", "partner_contract_id": "PARTNER_A", "is_excluded": 1},
        {"registry_id": "REG_B_001", "registry_date": "2025-01-15", "partner_contract_id": "PARTNER_B", "is_excluded": 0},
        {"registry_id": "REG_B_002", "registry_date": "2025-01-15", "partner_contract_id": "PARTNER_B", "is_excluded": 0}
    ],
    
    "commission_rates": [
        {"partner_contract_id": "PARTNER_A", "commission_percent": 0.02, "fixed_commission": 0.50, "start_date": "2025-01-01", "end_date": "2025-12-31"},
        {"partner_contract_id": "PARTNER_B", "commission_percent": 0.015, "fixed_commission": 1.00, "start_date": "2025-01-01", "end_date": "2025-12-31"}
    ]
}

# Расчет комиссий
def calculate_commissions():
    for op in DEMO_DATABASE["processing_operations"]:
        if op["status"] == "success" and op["commission_amount"] is None:
            rate = next(r for r in DEMO_DATABASE["commission_rates"] if r["partner_contract_id"] == op["partner_contract_id"])
            op["commission_amount"] = round(op["amount"] * rate["commission_percent"] + rate["fixed_commission"], 2)
    
    for payment in DEMO_DATABASE["partner_a_payments"]:
        if payment["commission"] is None and payment["status"] == "COMPLETED":
            op = next(op for op in DEMO_DATABASE["processing_operations"] if op["processing_id"] == payment["processing_id"])
            payment["commission"] = op["commission_amount"]
            
    for payment in DEMO_DATABASE["partner_b_payments"]:
        if payment["commission"] is None and payment["status"] == "SUCCESS":
            rate = next(r for r in DEMO_DATABASE["commission_rates"] if r["partner_contract_id"] == "PARTNER_B")
            add_data = next(add for add in DEMO_DATABASE["operation_additional_data"] 
                          if add["additional_value"] == payment["partner_id"] and add["additional_type"] == "partner_operation_id")
            op = next(op for op in DEMO_DATABASE["processing_operations"] if op["processing_id"] == add_data["processing_id"])
            payment["commission"] = round(op["amount"] * rate["commission_percent"] + rate["fixed_commission"], 2)

calculate_commissions()
