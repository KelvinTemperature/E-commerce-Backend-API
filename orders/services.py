import uuid
import requests
from django.conf import settings
from django.core.mail import send_mail

from store.models import Product
from .models import Order, OrderItem
from .logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────
# ORDER SERVICE
# ─────────────────────────────────────────────────────────────

def create_order(user, items_data):
    """
    Creates an Order and its OrderItems from validated serializer data.

    Flow:
    1. Create the Order (status=PENDING)
    2. For each item: fetch product, snapshot price, create OrderItem
    3. Deduct stock from each product
    4. Calculate and save total_price on the order

    Args:
        user       : the authenticated User placing the order
        items_data : validated list from OrderSerializer
                     e.g. [{'product_id': 1, 'quantity': 2}, ...]

    Returns:
        Order instance
    """
    logger.info(f"Creating order for user: {user.email}")

    # Step 1 — Create the order shell
    order = Order.objects.create(user=user)

    # Step 2 — Create order items
    for item in items_data:
        product    = Product.objects.get(pk=item['product_id'])
        unit_price = product.price
        quantity   = item['quantity']

        OrderItem.objects.create(
            order      = order,
            product    = product,
            quantity   = quantity,
            unit_price = unit_price,
            subtotal   = unit_price * quantity   # also auto-calc'd in model.save()
        )

        # Step 3 — Deduct stock
        product.stock -= quantity
        product.save()

        logger.info(
            f"  Item added: {quantity} × {product.name} "
            f"@ {unit_price} — stock remaining: {product.stock}"
        )

    # Step 4 — Calculate total
    order.calculate_total()

    logger.info(
        f"Order #{order.id} created — "
        f"total: {order.total_price} — status: {order.status}"
    )

    return order


# ─────────────────────────────────────────────────────────────
# PAYMENT SERVICE
# ─────────────────────────────────────────────────────────────

def initiate_payment(order):
    """
    Calls Paystack's /transaction/initialize endpoint to create
    a payment session for the given order.

    Flow:
    1. Build payload with amount, email, reference
    2. POST to Paystack API
    3. On success → return authorization_url + reference
    4. On failure → raise Exception

    Args:
        order : Order instance (must have total_price and user)

    Returns:
        dict with keys: authorization_url, reference
    """
    # Paystack expects amount in KOBO (smallest currency unit)
    # So multiply by 100: ₦49.99 → 4999 kobo
    amount_in_kobo = int(order.total_price * 100)

    # Generate a unique reference for this payment attempt
    reference = f"ORDER-{order.id}-{uuid.uuid4().hex[:8].upper()}"

    payload = {
        'email':     order.user.email,
        'amount':    amount_in_kobo,
        'reference': reference,
        'metadata': {
            'order_id':   order.id,
            'user_email': order.user.email,
        }
    }

    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type':  'application/json',
    }

    logger.info(
        f"Initiating payment for Order #{order.id} — "
        f"amount: {order.total_price} — reference: {reference}"
    )

    try:
        response = requests.post(
            f"{settings.PAYSTACK_BASE_URL}/transaction/initialize",
            json    = payload,
            headers = headers,
            timeout = 10    # fail fast if Paystack is slow
        )
        response.raise_for_status()   
        data = response.json()

        if not data.get('status'):
            logger.error(
                f"Paystack rejected payment for Order #{order.id}: "
                f"{data.get('message')}"
            )
            raise Exception(f"Paystack error: {data.get('message')}")

        authorization_url = data['data']['authorization_url']

        logger.info(
            f"Payment initiated for Order #{order.id} — "
            f"reference: {reference}"
        )

        return {
            'authorization_url': authorization_url,
            'reference':         reference,
        }

    except requests.exceptions.Timeout:
        logger.error(f"Paystack timeout for Order #{order.id}")
        raise Exception("Payment gateway timed out. Please try again.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack request failed for Order #{order.id}: {str(e)}")
        raise Exception(f"Payment gateway error: {str(e)}")


def verify_payment(reference):
    """
    Calls Paystack's /transaction/verify endpoint to confirm
    whether a payment was successful.

    Flow:
    1. GET /transaction/verify/{reference}
    2. Check status field in response
    3. Return 'success' or 'failed'

    Args:
        reference : the payment reference string

    Returns:
        dict with keys: status ('success'|'failed'), amount, reference
    """
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }

    logger.info(f"Verifying payment — reference: {reference}")

    try:
        response = requests.get(
            f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}",
            headers = headers,
            timeout = 10
        )
        response.raise_for_status()
        data = response.json()

        if not data.get('status'):
            raise Exception(f"Paystack error: {data.get('message')}")

        transaction = data['data']
        status      = transaction.get('status')    # 'success' or 'failed'
        amount      = transaction.get('amount', 0) / 100   # convert back from kobo

        logger.info(
            f"Payment verification — reference: {reference} "
            f"status: {status} — amount: {amount}"
        )

        return {
            'status':    status,
            'amount':    amount,
            'reference': reference,
        }

    except requests.exceptions.Timeout:
        logger.error(f"Paystack verification timeout — reference: {reference}")
        raise Exception("Verification timed out. Please try again.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Paystack verification failed — reference: {reference}: {str(e)}")
        raise Exception(f"Payment verification error: {str(e)}")


def update_order_status(order, payment_status, reference):
    """
    Updates the order status based on payment result.

    Args:
        order          : Order instance
        payment_status : 'success' or 'failed' (from Paystack)
        reference      : payment reference string

    Returns:
        Updated Order instance
    """
    order.payment_reference = reference

    if payment_status == 'success':
        order.status = Order.Status.PAID
        logger.info(f"Order #{order.id} marked as PAID — reference: {reference}")
    else:
        order.status = Order.Status.FAILED
        logger.warning(f"Order #{order.id} marked as FAILED — reference: {reference}")

    order.save()
    return order


# ─────────────────────────────────────────────────────────────
# EMAIL SERVICE
# ─────────────────────────────────────────────────────────────

def send_order_confirmation(order):
    """
    Sends an order confirmation email after successful payment.

    Args:
        order : Order instance (should already be PAID)
    """
    subject = f"Order Confirmed — Order #{order.id}"

    # Build item list for email body
    item_lines = "\n".join([
        f"  - {item.product.name} × {item.quantity} @ ₦{item.unit_price} = ₦{item.subtotal}"
        for item in order.items.all()
    ])

    message = f"""
Hi {order.user.username},

Your order has been confirmed and payment received. 🎉

─────────────────────────────
Order Summary
─────────────────────────────
Order ID    : #{order.id}
Status      : {order.status.upper()}
Reference   : {order.payment_reference}

Items:
{item_lines}

─────────────────────────────
Total Paid  : ₦{order.total_price}
─────────────────────────────

Thank you for shopping with us!

— E-commerce Team
    """.strip()

    try:
        send_mail(
            subject                  = subject,
            message                  = message,
            from_email               = settings.DEFAULT_FROM_EMAIL,
            recipient_list           = [order.user.email],
            fail_silently            = False,
        )
        logger.info(
            f"Confirmation email sent for Order #{order.id} "
            f"to {order.user.email}"
        )

    except Exception as e:
        # Email failure should NOT break the payment flow
        # Log the error and move on
        logger.error(
            f"Failed to send confirmation email for "
            f"Order #{order.id}: {str(e)}"
        )