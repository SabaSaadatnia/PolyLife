import json
import uuid
from decimal import Decimal

from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from config.permissions import IsTeam4Admin
from store.models import Product


from .models import DiscountCode, Invoice, Order, OrderItem, Transaction
from .serializers import (
    ApplyCouponSerializer,
    CartAddSerializer,
    CartUpdateSerializer,
    CheckoutSerializer,
    InvoiceSerializer,
    OrderSerializer,
    DiscountCodeSerializer,
)

class AdminOrderListView(APIView):
    permission_classes = [IsTeam4Admin]

    def get(self, request):
        orders = Order.objects.all().order_by("-created_at")

        serializer = OrderSerializer(
            orders,
            many=True
        )

        return Response(serializer.data)


class AdminOrderDetailView(APIView):
    permission_classes = [IsTeam4Admin]

    def get(self, request, pk):
        order = Order.objects.filter(id=pk).first()

        if not order:
            return Response(
                {"error": "Order not found"},
                status=404
            )

        serializer = OrderSerializer(order)

        return Response(serializer.data)
    
class AdminOrderStatusUpdateView(APIView):
    permission_classes = [IsTeam4Admin]

    def patch(self, request, pk):
        order = Order.objects.filter(id=pk).first()

        if not order:
            return Response(
                {"error": "Order not found"},
                status=404
            )

        new_status = request.data.get("status")

        valid_statuses = [
            choice[0]
            for choice in Order.STATUS_CHOICES
        ]

        if new_status not in valid_statuses:
            return Response(
                {
                    "error": "Invalid status",
                    "allowed": valid_statuses,
                },
                status=400
            )

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        return Response(
            {
                "message": "Order status updated successfully",
                "order_id": order.id,
                "status": order.status,
            }
        )

CART_TIMEOUT_SECONDS = 60 * 60 * 24 * 30


def get_user_id(request):
    raw_user_id = request.headers.get("X-User-Id")

    if not raw_user_id:
        return None

    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        return None


def get_cart_key(user_id):
    return f"cart:user:{user_id}"


def get_cart(user_id):
    cart = cache.get(get_cart_key(user_id))

    if not isinstance(cart, dict):
        return {}

    return cart


def save_cart(user_id, cart):
    cache.set(
        get_cart_key(user_id),
        cart,
        timeout=CART_TIMEOUT_SECONDS,
    )


def clear_cart(user_id):
    cache.delete(get_cart_key(user_id))


def build_cart_response(cart):
    if not cart:
        return {
            "items": [],
            "total": "0.00",
        }

    product_ids = [int(product_id) for product_id in cart]

    products = {
        str(product.id): product
        for product in Product.objects.filter(
            id__in=product_ids,
            is_active=True,
            is_deleted=False,
        )
    }

    items = []
    total = Decimal("0.00")

    for product_id, quantity in cart.items():
        product = products.get(str(product_id))

        if product is None:
            continue

        subtotal = product.price * quantity
        total += subtotal

        items.append(
            {
                "product_id": product.id,
                "name": product.name,
                "price": str(product.price),
                "quantity": quantity,
                "subtotal": str(subtotal),
                "available_stock": product.stock_quantity,
            }
        )

    return {
        "items": items,
        "total": str(total),
    }


@api_view(["GET"])
def cart_detail(request):
    user_id = get_user_id(request)

    if user_id is None:
        return Response(
            {"error": "Authentication is required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return Response(build_cart_response(get_cart(user_id)))


@api_view(["POST"])
def cart_add(request):
    user_id = get_user_id(request)

    if user_id is None:
        return Response(
            {"error": "Authentication is required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    serializer = CartAddSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product_id = serializer.validated_data["product_id"]
    quantity = serializer.validated_data["quantity"]

    try:
        product = Product.objects.get(
            pk=product_id,
            is_active=True,
            is_deleted=False,
        )
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    cart = get_cart(user_id)
    key = str(product_id)
    new_quantity = cart.get(key, 0) + quantity

    if new_quantity > product.stock_quantity:
        return Response(
            {
                "error": "Insufficient stock.",
                "available_stock": product.stock_quantity,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    cart[key] = new_quantity
    save_cart(user_id, cart)

    return Response(
        {
            "message": "Product added to cart.",
            "cart": build_cart_response(cart),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def cart_update(request):
    user_id = get_user_id(request)

    if user_id is None:
        return Response(
            {"error": "Authentication is required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    serializer = CartUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product_id = serializer.validated_data["product_id"]
    quantity = serializer.validated_data["quantity"]
    key = str(product_id)

    cart = get_cart(user_id)

    if key not in cart:
        return Response(
            {"error": "Product is not in the cart."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if quantity == 0:
        cart.pop(key)
        save_cart(user_id, cart)

        return Response(
            {
                "message": "Product removed from cart.",
                "cart": build_cart_response(cart),
            }
        )

    try:
        product = Product.objects.get(
            pk=product_id,
            is_active=True,
            is_deleted=False,
        )
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if quantity > product.stock_quantity:
        return Response(
            {
                "error": "Insufficient stock.",
                "available_stock": product.stock_quantity,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    cart[key] = quantity
    save_cart(user_id, cart)

    return Response(
        {
            "message": "Cart updated.",
            "cart": build_cart_response(cart),
        }
    )


@api_view(["POST"])
def apply_coupon(request):
    user_id = get_user_id(request)

    if user_id is None:
        return Response(
            {"error": "Authentication is required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    serializer = ApplyCouponSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data["code"].strip().upper()

    try:
        coupon = DiscountCode.objects.get(
            code=code,
            is_deleted=False,
        )
    except DiscountCode.DoesNotExist:
        return Response(
            {"error": "Invalid discount code."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not coupon.is_valid():
        return Response(
            {"error": "Discount code is expired or unavailable."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cart_data = build_cart_response(get_cart(user_id))
    total = Decimal(cart_data["total"])
    MONEY_QUANTUM = Decimal("0.01")
    discount_amount = (
        total
        * coupon.discount_percent
        / Decimal("100")
    ).quantize(MONEY_QUANTUM)

    final_amount = (total - discount_amount).quantize(MONEY_QUANTUM)

    return Response(
        {
            "code": coupon.code,
            "discount_percent": str(coupon.discount_percent),
            "original_total": str(total),
            "discount_amount": str(discount_amount),
            "final_total": str(final_amount),
        }
    )


@api_view(["POST"])
def checkout(request):
    user_id = get_user_id(request)

    if user_id is None:
        return Response(
            {"error": "Authentication is required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    serializer = CheckoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    cart = get_cart(user_id)

    if not cart:
        return Response(
            {"error": "Cart is empty."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    discount_code = (
        serializer.validated_data.get("discount_code", "")
        .strip()
        .upper()
    )

    try:
        with transaction.atomic():
            product_ids = [int(product_id) for product_id in cart]

            locked_products = Product.objects.select_for_update().filter(
                id__in=product_ids,
                is_active=True,
                is_deleted=False,
            )

            products = {
                str(product.id): product
                for product in locked_products
            }

            if len(products) != len(cart):
                return Response(
                    {"error": "One or more products are unavailable."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            total = Decimal("0.00")

            for product_id, quantity in cart.items():
                product = products.get(str(product_id))

                if product is None:
                    return Response(
                        {"error": f"Product {product_id} was not found."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if quantity > product.stock_quantity:
                    return Response(
                        {
                            "error": (
                                f"Insufficient stock for {product.name}."
                            ),
                            "available_stock": product.stock_quantity,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                total += product.price * quantity

            coupon = None
            discount_amount = Decimal("0.00")

            if discount_code:
                try:
                    coupon = (
                        DiscountCode.objects
                        .select_for_update()
                        .get(
                            code=discount_code,
                            is_deleted=False,
                        )
                    )
                except DiscountCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid discount code."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not coupon.is_valid():
                    return Response(
                        {
                            "error": (
                                "Discount code is expired or unavailable."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                discount_amount = (
                    total
                    * coupon.discount_percent
                    / Decimal("100")
                )

            final_amount = total - discount_amount

            order = Order.objects.create(
                user_id=user_id,
                discount_code=coupon,
                total_amount=total,
                discount_amount=discount_amount,
                final_amount=final_amount,
                status=Order.STATUS_PENDING,
            )

            for product_id, quantity in cart.items():
                product = products[str(product_id)]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                )

                Product.objects.filter(pk=product.pk).update(
                    stock_quantity=F("stock_quantity") - quantity,
                )

            transaction_reference = (
                f"TXN-{uuid.uuid4().hex[:12].upper()}"
            )

            Transaction.objects.create(
                order=order,
                transaction_ref=transaction_reference,
                amount=final_amount,
                status="success",
                gateway_response=json.dumps(
                    {
                        "gateway": "mock",
                        "reference": transaction_reference,
                        "timestamp": timezone.now().isoformat(),
                    }
                ),
            )

            order.status = Order.STATUS_PAID
            order.save(update_fields=["status", "updated_at"])

            if coupon is not None:
                coupon.used_count = F("used_count") + 1
                coupon.save(update_fields=["used_count", "updated_at"])

            invoice = Invoice.objects.create(
                order=order,
                invoice_number=(
                    f"INV-{order.id:08d}-"
                    f"{uuid.uuid4().hex[:4].upper()}"
                ),
                user_id=user_id,
            )

    except (TypeError, ValueError):
        return Response(
            {"error": "Cart data is invalid."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    clear_cart(user_id)

    return Response(
        {
            "message": "Mock payment completed successfully.",
            "order_id": order.id,
            "invoice_number": invoice.invoice_number,
            "transaction_ref": transaction_reference,
            "total_paid": str(final_amount),
            "payment_gateway": "mock",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def order_history(request):
    user_id = get_user_id(request)

    if user_id is None:
        return Response(
            {"error": "Authentication is required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    orders = (
        Order.objects.filter(
            user_id=user_id,
            is_deleted=False,
        )
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    return Response(OrderSerializer(orders, many=True).data)


@api_view(["GET"])
def invoice_detail(request, invoice_number):
    user_id = get_user_id(request)

    if user_id is None:
        return Response(
            {"error": "Authentication is required."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        invoice = (
            Invoice.objects
            .select_related("order")
            .prefetch_related("order__items__product")
            .get(
                invoice_number=invoice_number,
                user_id=user_id,
                is_deleted=False,
            )
        )
    except Invoice.DoesNotExist:
        return Response(
            {"error": "Invoice not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(InvoiceSerializer(invoice).data)


class AdminDiscountListCreateView(APIView):
    permission_classes = [IsTeam4Admin]

    def get(self, request):
        discounts = DiscountCode.objects.all().order_by("-created_at")

        serializer = DiscountCodeSerializer(
            discounts,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = DiscountCodeSerializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=201
            )

        return Response(
            serializer.errors,
            status=400
        )


class AdminDiscountDetailView(APIView):
    permission_classes = [IsTeam4Admin]

    def put(self, request, pk):
        discount = DiscountCode.objects.filter(id=pk).first()

        if not discount:
            return Response(
                {"error": "Discount code not found"},
                status=404
            )

        serializer = DiscountCodeSerializer(
            discount,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=400
        )

    def delete(self, request, pk):
        discount = DiscountCode.objects.filter(id=pk).first()

        if not discount:
            return Response(
                {"error": "Discount code not found"},
                status=404
            )

        discount.is_active = False
        discount.save(update_fields=["is_active"])

        return Response(
            {"message": "Discount code deactivated successfully"}
        )
    
    