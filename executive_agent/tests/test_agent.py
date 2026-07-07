"""Tests for agent tool selection and response contracts."""

import pytest

from app.agents.executive_agent import ExecutiveCommerceAgent
from app.schemas.tools import ToolCall


class FakeTools:
    """Deterministic tool double for agent workflow tests."""

    async def get_order_by_order_number(self, order_number: str) -> dict:
        return {"orderNumber": order_number}

    async def get_products_by_name(self, product_name: str) -> list[dict]:
        return [{"productName": product_name}]

    async def get_inventory_by_sku(self, sku: str) -> dict:
        return {"sku": sku, "availableQuantity": 5}

    async def get_customer_by_email(self, email: str) -> dict:
        return {"email": email}

    async def get_customer_order_history_by_email(self, email: str) -> dict:
        return {"customerEmail": email, "totalOrders": 2, "orders": []}


class ProviderDrivenSelection:
    """Test double that proves the agent defers tool choice to the provider."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[dict[str, object]]]] = []

    async def select_tool(self, prompt: str, tools: list[dict[str, object]]) -> ToolCall:
        self.calls.append((prompt, tools))
        return ToolCall(name="get_inventory_by_sku", arguments={"sku": "TLSS-01"})


@pytest.mark.asyncio
async def test_selects_tool_via_provider() -> None:
    """Tool selection is delegated to the LLM provider."""

    provider = ProviderDrivenSelection()
    agent = ExecutiveCommerceAgent(tools=FakeTools(), provider=provider)
    call = await agent.select_tool("Order details for order number 100001")
    assert call.name == "get_inventory_by_sku"
    assert call.arguments == {"sku": "TLSS-01"}
    assert provider.calls[0][0] == "Order details for order number 100001"
    assert len(provider.calls[0][1]) == 5


def test_agent_uses_langgraph_and_langchain_tools() -> None:
    """The agent owns a compiled LangGraph workflow and LangChain tools."""

    agent = ExecutiveCommerceAgent(tools=FakeTools(), provider=ProviderDrivenSelection())
    assert hasattr(agent.graph, "ainvoke")
    assert "get_order_by_order_number" in agent.langchain_tools
    assert hasattr(agent.langchain_tools["get_order_by_order_number"], "ainvoke")


@pytest.mark.asyncio
async def test_agent_returns_standard_contract() -> None:
    """Successful agent runs return the standard response schema."""

    class SuccessProvider(ProviderDrivenSelection):
        async def select_tool(self, prompt: str, tools: list[dict[str, object]]) -> ToolCall:
            self.calls.append((prompt, tools))
            return ToolCall(name="get_inventory_by_sku", arguments={"sku": "TLSS-01"})

        async def generate_response(self, prompt: str, tool_name: str, data: object) -> str:
            return "Inventory retrieved."

    agent = ExecutiveCommerceAgent(tools=FakeTools(), provider=SuccessProvider())
    response = await agent.run("Inventory for TLSS-01")
    assert response.success is True
    assert response.userQuery == "Inventory for TLSS-01"
    assert response.toolUsed == "get_inventory_by_sku"
    assert response.error is None
