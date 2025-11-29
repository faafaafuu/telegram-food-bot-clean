import asyncio

async def process_payment_mock(order_id: int, amount: float, method: str):
    # Simulate contacting payment gateway
    await asyncio.sleep(1.0)
    # For mock: succeed for online, or return pending for cash
    if method == 'online':
        return {'status': 'paid', 'transaction_id': f'mock_{order_id}'}
    elif method == 'card_on_delivery':
        return {'status': 'reserved', 'transaction_id': None}
    else:
        return {'status': 'cash', 'transaction_id': None}
