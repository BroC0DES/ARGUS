from mock_codebase.database_service.db import save_payment


def process_payment():
    print("Payment Service: Processing payment")

    payment_saved = save_payment()

    if payment_saved:
        print("Payment Service: Payment processed successfully")
        return True

    print("Payment Service: Payment processing failed")
    return False