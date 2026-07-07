"""LangChain tool wrappers around normalized commercetools business tools."""

from langchain_core.tools import StructuredTool

from app.tools.commerce_tools import CommerceTools


def build_langchain_tools(tools: CommerceTools) -> dict[str, StructuredTool]:
    """Create LangChain StructuredTool adapters for the existing async tool methods."""

    return {
        "get_order_by_order_number": StructuredTool.from_function(
            coroutine=tools.get_order_by_order_number,
            name="get_order_by_order_number",
            description="Show order by order number.",
        ),
        "get_products_by_name": StructuredTool.from_function(
            coroutine=tools.get_products_by_name,
            name="get_products_by_name",
            description="Search product by name.",
        ),
        "get_inventory_by_sku": StructuredTool.from_function(
            coroutine=tools.get_inventory_by_sku,
            name="get_inventory_by_sku",
            description="Retrieve inventory information for a product SKU.",
        ),
        "get_customer_by_email": StructuredTool.from_function(
            coroutine=tools.get_customer_by_email,
            name="get_customer_by_email",
            description="Retrieve customer details using the customer's email address.",
        ),
        "get_customer_order_history_by_email": StructuredTool.from_function(
            coroutine=tools.get_customer_order_history_by_email,
            name="get_customer_order_history_by_email",
            description="Retrieve complete order history for a customer email address.",
        ),
    }
