"""Deterministic local response provider used when SDKs or API keys are unavailable."""

from typing import Any

from app.providers.base import LLMProvider
from app.providers.http_helpers import build_tool_selection_messages
from app.schemas.tools import ToolCall, ToolSpec


class TemplateProvider(LLMProvider):
    """Create concise responses without making an external LLM call."""

    async def generate_response(self, prompt: str, tool_name: str, data: Any) -> str:
        """Generate a business-readable response for normalized tool output."""

        if tool_name == "get_order_by_order_number":
            return f"Order {data.get('orderNumber')} has been successfully retrieved."
        if tool_name == "get_products_by_name":
            return f"Found {len(data)} matching product result(s)."
        if tool_name == "get_inventory_by_sku":
            return f"SKU {data.get('sku')} has {data.get('availableQuantity')} available units."
        if tool_name == "get_customer_by_email":
            return f"Customer {data.get('email')} has been successfully retrieved."
        if tool_name == "get_customer_order_history_by_email":
            return f"Customer {data.get('customerEmail')} has {data.get('totalOrders')} order(s)."
        return "The requested commerce insight has been retrieved."

    async def select_tool(self, prompt: str, tools: list[ToolSpec]) -> ToolCall:
        """Fallback tool selection using deterministic keyword matching."""

        lowered = prompt.lower()
        if any(term in lowered for term in ("history", "orders", "order history", "purchases")):
            return ToolCall(name="get_customer_order_history_by_email", arguments={"email": self._find_email(prompt)})
        if "@" in prompt:
            return ToolCall(name="get_customer_by_email", arguments={"email": self._find_email(prompt)})
        if any(term in lowered for term in ("inventory", "stock", "sku")):
            return ToolCall(name="get_inventory_by_sku", arguments={"sku": self._find_sku(prompt)})
        if "order" in lowered:
            return ToolCall(name="get_order_by_order_number", arguments={"order_number": self._find_order_number(prompt)})
        return ToolCall(name="get_products_by_name", arguments={"product_name": prompt.strip()})

    @staticmethod
    def _find_email(prompt: str) -> str:
        """Extract a first-pass email from a prompt."""

        for token in prompt.split():
            if "@" in token:
                return token.strip(".,")
        return ""

    @staticmethod
    def _find_sku(prompt: str) -> str:
        """Extract a first-pass SKU from a prompt."""

        for token in prompt.split():
            if "-" in token and any(ch.isdigit() for ch in token):
                return token.strip(".,")
        return ""

    @staticmethod
    def _find_order_number(prompt: str) -> str:
        """Extract a first-pass order number from a prompt."""

        for token in prompt.split():
            if token.isdigit():
                return token
        return ""
