from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Order
from .serializers import OrderSerializer, OrderDetailSerializer
from .logger import get_logger
from . import services

logger = get_logger(__name__)


class OrderListView(APIView):
    """
    GET  /api/orders/   → list all orders belonging to logged-in user
    POST /api/orders/   → create a new order
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            user=request.user
        ).prefetch_related('items__product').order_by('-created_at')
        # prefetch_related → fetches items + products in 2 extra queries
        # instead of N queries (one per item) — much more efficient

        serializer = OrderDetailSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = OrderSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(
                f"Invalid order data from {request.user.email}: "
                f"{serializer.errors}"
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = services.create_order(
                user       = request.user,
                items_data = serializer.validated_data['items']
            )
            response_serializer = OrderDetailSerializer(order)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(
                f"Order creation failed for {request.user.email}: {str(e)}"
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderDetailView(APIView):
    """
    GET /api/orders/<id>/  → get a single order (must belong to logged-in user)
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            # Filter by both pk AND user — users can only see their own orders
            return Order.objects.prefetch_related(
                'items__product'
            ).get(pk=pk, user=user)
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        order = self.get_object(pk, request.user)

        if order is None:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderPaymentView(APIView):
    """
    POST /api/orders/<id>/pay/

    Initiates a Paystack payment for the given order.
    Only works if the order is PENDING — prevents double payment.

    Returns a Paystack authorization_url the user visits to pay.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # Fetch order — must belong to this user
        try:
            order = Order.objects.get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Guard — only PENDING orders can be paid
        if order.status != Order.Status.PENDING:
            logger.warning(
                f"Payment attempted on non-pending Order #{order.id} "
                f"by {request.user.email} — current status: {order.status}"
            )
            return Response(
                {
                    'error': (
                        f"This order cannot be paid. "
                        f"Current status: {order.status}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment_data = services.initiate_payment(order)

            return Response(
                {
                    'message':           'Payment initiated successfully.',
                    'order_id':          order.id,
                    'authorization_url': payment_data['authorization_url'],
                    'reference':         payment_data['reference'],
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(
                f"Payment initiation failed for Order #{order.id}: {str(e)}"
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY
                # 502 = upstream service (Paystack) failed
            )


class OrderVerifyView(APIView):
    """
    POST /api/orders/<id>/verify/

    Verifies a Paystack payment and updates order status.

    Expected body:
    { "reference": "ORDER-1-A3F9B2C1" }

    Flow:
    1. Verify payment with Paystack
    2. Update order status → PAID or FAILED
    3. If PAID → send confirmation email
    4. Return updated order
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # Fetch order
        try:
            order = Order.objects.prefetch_related(
                'items__product'
            ).get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Guard — only PENDING orders need verification
        if order.status != Order.Status.PENDING:
            return Response(
                {
                    'error': (
                        f"Order is already {order.status}. "
                        f"Verification not required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get reference from request body
        reference = request.data.get('reference')
        if not reference:
            return Response(
                {'error': 'Payment reference is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Step 1 — Verify with Paystack
            payment_result = services.verify_payment(reference)

            # Step 2 — Update order status
            order = services.update_order_status(
                order          = order,
                payment_status = payment_result['status'],
                reference      = reference
            )

            # Step 3 — Send email if paid
            if order.status == Order.Status.PAID:
                services.send_order_confirmation(order)

            # Step 4 — Return updated order
            serializer = OrderDetailSerializer(order)
            return Response(
                {
                    'message': (
                        'Payment verified successfully.'
                        if order.status == Order.Status.PAID
                        else 'Payment failed. Please try again.'
                    ),
                    'order': serializer.data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(
                f"Payment verification failed for Order #{order.id}: {str(e)}"
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )