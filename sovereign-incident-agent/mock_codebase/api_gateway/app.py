from mock_codebase.order_service.order import create_order


def checkout():
    print("API Gateway: Checkout request received")

    result = create_order()

    if result:
        print("API Gateway: Order completed")
    else:
        print("API Gateway: Order failed")


if __name__ == "__main__":
    checkout()