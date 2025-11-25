# Схема базы данных DataWork Lab
DATABASE_SCHEMA = {
    "processing_operations": {
        "description": "Основная таблица операций нашего процессинга",
        "columns": {
            "processing_id": {
                "type": "VARCHAR", 
                "pk": True, 
                "description": "Уникальный ID операции в нашей системе"
            },
            "created_date": {
                "type": "DATE", 
                "description": "Дата создания операции"
            },
            "finalized_date": {
                "type": "DATE", 
                "description": "Дата финализации операции (когда стал известен итоговый статус)"
            },
            "amount": {
                "type": "DECIMAL(10,2)", 
                "description": "Сумма операции в валюте"
            },
            "currency": {
                "type": "VARCHAR", 
                "description": "Валюта операции (все операции в EUR)"
            },
            "status": {
                "type": "VARCHAR", 
                "description": "Текущий статус операции: success, failed, pending"
            },
            "commission_amount": {
                "type": "DECIMAL(10,2)", 
                "description": "Рассчитанная сумма комиссии (только для успешных операций)"
            },
            "partner_contract_id": {
                "type": "VARCHAR", 
                "fk": "commission_rates",
                "description": "ID партнера для связи с таблицей ставок комиссий"
            }
        }
    },
    "partner_a_payments": {
        "description": "Реестр операций от Партнера А",
        "columns": {
            "partner_id": {
                "type": "VARCHAR", 
                "pk": True, 
                "description": "Уникальный ID операции у Партнера А"
            },
            "processing_id": {
                "type": "VARCHAR", 
                "fk": "processing_operations",
                "description": "Связь с нашей операцией (может быть NULL)"
            },
            "status": {
                "type": "VARCHAR", 
                "description": "Статус операции у партнера: COMPLETED, DECLINED, IN_PROGRESS"
            },
            "commission": {
                "type": "DECIMAL(10,2)", 
                "description": "Комиссия указанная в реестре партнера"
            },
            "registry_id": {
                "type": "VARCHAR", 
                "fk": "registry_statuses",
                "description": "ID реестра в котором пришла операция"
            }
        }
    },
    "partner_b_payments": {
        "description": "Реестр операций от Партнера Б",
        "columns": {
            "partner_id": {
                "type": "VARCHAR", 
                "pk": True, 
                "description": "Уникальный ID операции у Партнера Б"
            },
            "status": {
                "type": "VARCHAR", 
                "description": "Статус операции у партнера: SUCCESS, FAILED"
            },
            "commission": {
                "type": "DECIMAL(10,2)", 
                "description": "Комиссия указанная в реестре партнера"
            },
            "registry_id": {
                "type": "VARCHAR", 
                "fk": "registry_statuses",
                "description": "ID реестра в котором пришла операция"
            }
        }
    },
    "operation_additional_data": {
        "description": "Дополнительные данные для операций (нормализованный формат)",
        "columns": {
            "processing_id": {
                "type": "VARCHAR", 
                "fk": "processing_operations",
                "description": "Связь с нашей операцией"
            },
            "created_date": {
                "type": "DATE", 
                "description": "Дата создания записи"
            },
            "additional_type": {
                "type": "VARCHAR", 
                "description": "Тип дополнительных данных: partner_operation_id, card_country, card_masked"
            },
            "additional_value": {
                "type": "VARCHAR", 
                "description": "Значение дополнительных данных"
            }
        }
    },
    "registry_statuses": {
        "description": "Статусы реестров от партнеров",
        "columns": {
            "registry_id": {
                "type": "VARCHAR", 
                "pk": True, 
                "description": "Уникальный ID реестра"
            },
            "registry_date": {
                "type": "DATE", 
                "description": "Дата реестра"
            },
            "partner_contract_id": {
                "type": "VARCHAR", 
                "description": "ID партнера которому принадлежит реестр"
            },
            "is_excluded": {
                "type": "INTEGER", 
                "description": "Флаг исключения реестра: 0 - активен, 1 - исключен (не учитывать)"
            }
        }
    },
    "commission_rates": {
        "description": "Ставки комиссий по партнерам",
        "columns": {
            "partner_contract_id": {
                "type": "VARCHAR", 
                "pk": True, 
                "description": "ID партнера"
            },
            "commission_percent": {
                "type": "DECIMAL(5,4)", 
                "description": "Процентная ставка комиссии (например 0.02 для 2%)"
            },
            "fixed_commission": {
                "type": "DECIMAL(10,2)", 
                "description": "Фиксированная часть комиссии"
            },
            "start_date": {
                "type": "DATE", 
                "description": "Дата начала действия ставки"
            },
            "end_date": {
                "type": "DATE", 
                "description": "Дата окончания действия ставки"
            }
        }
    }
}
