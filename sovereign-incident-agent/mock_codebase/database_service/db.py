from mock_codebase.database_service.connection import connect


def save_payment():
    print("Database Service: Saving payment")

    if connect():
        print("Database Service: Payment saved")
        return True

    return False


def save_inventory():
    print("Database Service: Checking inventory")

    if connect():
        print("Database Service: Inventory check successful")
        return True

    return False