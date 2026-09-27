from mock_codebase.payment_service.payment import process_payment
from mock_codebase.inventory_service.inventory import check_inventory


def create_order():
    print("Order Service: Creating order")

    if not check_inventory():
        print("Order Service: Inventory unavailable")
        return False

    payment_result = process_payment()

    if payment_result:
        print("Order Service: Order created successfully")
        return True

    print("Order Service: Payment failed")
    return False