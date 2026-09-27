from mock_codebase.database_service.db import save_inventory


def check_inventory():
    print("Inventory Service: Checking inventory")

    result = save_inventory()

    if result:
        print("Inventory Service: Inventory available")
        return True

    print("Inventory Service: Inventory check failed")
    return False