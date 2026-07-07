"""Tests for commercetools response normalization."""

from app.tools.normalizers import normalize_customer, normalize_order, normalize_product_projection


def test_normalize_order_keeps_business_fields() -> None:
    """Order normalization strips raw fields and converts money."""

    payload = {
        "id": "internal",
        "orderNumber": "100001",
        "customerEmail": "seb@example.de",
        "createdAt": "2026-04-15T15:39:51.209Z",
        "orderState": "Confirmed",
        "paymentState": "Paid",
        "shipmentState": "Ready",
        "totalPrice": {"currencyCode": "EUR", "centAmount": 409900, "fractionDigits": 2},
        "shippingAddress": {"firstName": "Sebastian", "lastName": "Muller", "city": "Munich", "country": "DE"},
        "lineItems": [
            {
                "name": {"en-US": "Traditional L Seater Sofa"},
                "variant": {"sku": "TLSS-01"},
                "quantity": 1,
                "price": {"value": {"currencyCode": "EUR", "centAmount": 359900, "fractionDigits": 2}},
            }
        ],
    }
    normalized = normalize_order(payload)
    assert normalized["orderNumber"] == "100001"
    assert normalized["totalPrice"] == {"currency": "EUR", "amount": 4099}
    assert normalized["items"][0]["sku"] == "TLSS-01"
    assert "id" not in normalized


def test_normalize_product_projection() -> None:
    """Product projection normalization extracts sku, price, and inventory."""

    payload = {
        "id": "p1",
        "key": "traditional-l-seater-sofa",
        "name": {"en-US": "Traditional L Seater Sofa"},
        "masterVariant": {
            "sku": "TLSS-01",
            "prices": [{"value": {"currencyCode": "EUR", "centAmount": 359900, "fractionDigits": 2}}],
            "availability": {"isOnStock": True, "availableQuantity": 98},
        },
    }
    normalized = normalize_product_projection(payload)
    assert normalized["productName"] == "Traditional L Seater Sofa"
    assert normalized["price"]["amount"] == 3599
    assert normalized["inventory"]["availableQuantity"] == 98


def test_normalize_customer_addresses() -> None:
    """Customer normalization marks shipping and billing addresses."""

    payload = {
        "id": "c1",
        "firstName": "Jennifer",
        "lastName": "Robinson",
        "email": "jen@example.com",
        "isEmailVerified": True,
        "shippingAddressIds": ["a1"],
        "billingAddressIds": ["a2"],
        "addresses": [{"id": "a1", "city": "New York City", "country": "US"}],
    }
    normalized = normalize_customer(payload)
    assert normalized["customerId"] == "c1"
    assert normalized["addresses"][0]["isShippingAddress"] is True
    assert normalized["addresses"][0]["isBillingAddress"] is False
