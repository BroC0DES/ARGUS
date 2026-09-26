from services.orders_service.submit import submit_order


def handle_checkout(request):
    """Public POST /checkout entrypoint. Forwards to orders-service."""
    order = request.json()
    result = submit_order(order)
    return {"status": 200, "order": result}
