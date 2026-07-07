"""Normalize raw commercetools payloads into compact business JSON."""

from typing import Any


def money(value: dict[str, Any] | None) -> dict[str, Any]:
    """Convert commercetools centAmount money into currency and decimal amount."""

    if not value:
        return {"currency": "", "amount": 0}
    cent_amount = value.get("centAmount", 0)
    fraction_digits = value.get("fractionDigits", 2)
    return {"currency": value.get("currencyCode", ""), "amount": cent_amount / (10**fraction_digits)}


def localized_name(value: dict[str, Any] | str | None) -> str:
    """Return a readable localized name from commercetools localized fields."""

    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ""
    for locale in ("en-US", "en", "de-DE", "de", "en-GB"):
        if locale in value:
            return str(value[locale])
    return str(next(iter(value.values()), ""))


def normalize_order(order: dict[str, Any]) -> dict[str, Any]:
    """Normalize a commercetools order into the dashboard contract shape."""

    shipping = order.get("shippingAddress") or {}
    items = []
    for item in order.get("lineItems", []):
        price_value = ((item.get("price") or {}).get("value") or item.get("totalPrice") or {})
        items.append(
            {
                "name": localized_name(item.get("name")),
                "sku": item.get("variant", {}).get("sku", ""),
                "quantity": item.get("quantity", 0),
                "price": money(price_value)["amount"],
                "currency": money(price_value)["currency"],
            }
        )

    total_price = money(order.get("totalPrice"))
    return {
        "orderNumber": order.get("orderNumber"),
        "customerEmail": order.get("customerEmail", ""),
        "createdAt": order.get("createdAt", ""),
        "orderState": order.get("orderState", ""),
        "paymentState": order.get("paymentState", ""),
        "shipmentState": order.get("shipmentState", ""),
        "country": shipping.get("country", ""),
        "totalPrice": total_price,
        "shippingAddress": {
            "name": " ".join(part for part in [shipping.get("firstName"), shipping.get("lastName")] if part),
            "city": shipping.get("city", ""),
            "country": shipping.get("country", ""),
        },
        "items": items,
    }


def normalize_product_projection(product: dict[str, Any]) -> dict[str, Any]:
    """Normalize a commercetools product projection search result."""

    master = product.get("masterVariant") or {}
    first_price = (master.get("prices") or [{}])[0]
    availability = master.get("availability") or {}
    return {
        "id": product.get("id", ""),
        "productName": localized_name(product.get("name")),
        "productKey": product.get("key", ""),
        "sku": master.get("sku", ""),
        "price": money(first_price.get("value")),
        "inventory": {
            "isOnStock": availability.get("isOnStock", False),
            "availableQuantity": availability.get("availableQuantity", 0),
        },
    }


def normalize_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize an inventory search response for one SKU."""

    result = (payload.get("results") or [{}])[0]
    return {
        "sku": result.get("sku", ""),
        "quantityOnStock": result.get("quantityOnStock", 0),
        "availableQuantity": result.get("availableQuantity", 0),
    }


def normalize_customer(customer: dict[str, Any]) -> dict[str, Any]:
    """Normalize a customer record for business-facing output."""

    shipping_ids = set(customer.get("shippingAddressIds") or [])
    billing_ids = set(customer.get("billingAddressIds") or [])
    addresses = []
    for address in customer.get("addresses", []):
        address_id = address.get("id", "")
        addresses.append(
            {
                "addressId": address_id,
                "firstName": address.get("firstName", ""),
                "lastName": address.get("lastName", ""),
                "street": address.get("streetName", ""),
                "city": address.get("city", ""),
                "state": address.get("state", ""),
                "postalCode": address.get("postalCode", ""),
                "country": address.get("country", ""),
                "isShippingAddress": address_id in shipping_ids,
                "isBillingAddress": address_id in billing_ids,
            }
        )
    return {
        "customerId": customer.get("id", ""),
        "firstName": customer.get("firstName", ""),
        "lastName": customer.get("lastName", ""),
        "email": customer.get("email", ""),
        "isEmailVerified": customer.get("isEmailVerified", False),
        "addresses": addresses,
    }


def normalize_customer_order_history(email: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize an order collection for a customer's order history."""

    orders = []
    for order in payload.get("results", []):
        total = money(order.get("totalPrice"))
        orders.append(
            {
                "orderNumber": order.get("orderNumber"),
                "orderId": order.get("id", ""),
                "orderDate": order.get("createdAt", ""),
                "orderState": order.get("orderState", ""),
                "paymentState": order.get("paymentState", ""),
                "shipmentState": order.get("shipmentState", ""),
                "currency": total["currency"],
                "totalAmount": total["amount"],
            }
        )
    return {"customerEmail": email, "totalOrders": len(orders), "orders": orders}
