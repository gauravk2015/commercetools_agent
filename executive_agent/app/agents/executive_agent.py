"""Executive commerce agent orchestration and tool selection."""

from langgraph.graph import END, START, StateGraph

from app.models.errors import AgentError, CommerceToolsError
from app.agents.langgraph_state import ExecutiveAgentState
from app.providers.base import LLMProvider
from app.providers.factory import LLMFactory
from app.schemas.chat import AgentResponse, ErrorInfo
from app.schemas.tools import ToolCall, ToolSpec
from app.tools import CommerceTools
from app.tools.langchain_tools import build_langchain_tools
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ExecutiveCommerceAgent:
    """Select tools, execute normalized commerce lookups, and shape responses."""

    def __init__(self, tools: CommerceTools | None = None, provider: LLMProvider | None = None) -> None:
        self.tools = tools or CommerceTools()
        self.provider = provider or LLMFactory.create()
        self.langchain_tools = build_langchain_tools(self.tools)
        self.tool_specs = self._tool_specs()
        self.graph = self._build_graph()

    async def run(self, prompt: str) -> AgentResponse:
        """Run the end-to-end agent workflow for a prompt."""

        try:
            final_state = await self.graph.ainvoke({"prompt": prompt})
            if final_state.get("error_code"):
                return AgentResponse(
                    success=False,
                    userQuery=prompt,
                    toolUsed=final_state.get("tool_name"),
                    response=final_state["error_message"],
                    data=None,
                    error=ErrorInfo(code=final_state["error_code"], message=final_state["error_message"]),
                )
            return AgentResponse(
                success=True,
                userQuery=prompt,
                toolUsed=final_state["tool_name"],
                response=final_state["response"],
                data=final_state["data"],
                error=None,
            )
        except AgentError:
            raise

    async def select_tool(self, prompt: str) -> ToolCall:
        """Ask the configured LLM to select the correct business tool."""

        tool_call = await self.provider.select_tool(prompt, self.tool_specs)
        if tool_call.name not in self.langchain_tools:
            raise AgentError(
                "UNSUPPORTED_REQUEST",
                "Please ask about an order number, product name, SKU inventory, customer email, or customer order history.",
            )
        return tool_call

    def _build_graph(self):
        """Compile the LangGraph workflow used by the agent."""

        workflow = StateGraph(ExecutiveAgentState)
        workflow.add_node("select_tool", self._select_tool_node)
        workflow.add_node("execute_tool", self._execute_tool_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_edge(START, "select_tool")
        workflow.add_edge("select_tool", "execute_tool")
        workflow.add_edge("execute_tool", "generate_response")
        workflow.add_edge("generate_response", END)
        return workflow.compile()

    async def _select_tool_node(self, state: ExecutiveAgentState) -> ExecutiveAgentState:
        """LangGraph node that selects the business tool for the prompt."""

        tool_call = await self.select_tool(state["prompt"])
        logger.info("agent_selected_tool tool=%s", tool_call.name)
        return {"tool_call": tool_call, "tool_name": tool_call.name}

    async def _execute_tool_node(self, state: ExecutiveAgentState) -> ExecutiveAgentState:
        """LangGraph node that invokes the selected LangChain tool."""

        tool_call = state["tool_call"]
        selected_tool = self.langchain_tools[tool_call.name]
        try:
            data = await selected_tool.ainvoke(tool_call.arguments)
            return {"data": data}
        except CommerceToolsError as exc:
            return {
                "error_code": exc.code,
                "error_message": exc.message,
                "tool_name": exc.tool_name or tool_call.name,
            }

    async def _generate_response_node(self, state: ExecutiveAgentState) -> ExecutiveAgentState:
        """LangGraph node that generates the final natural language response."""

        if state.get("error_code"):
            return {}
        response = await self.provider.generate_response(state["prompt"], state["tool_name"], state["data"])
        return {"response": response}

    @staticmethod
    def _tool_specs() -> list[ToolSpec]:
        """Return the tool catalog presented to the LLM."""

        return [
            {
                "name": "get_order_by_order_number",
                "description": "Order Lookup. Retrieve complete order details instantly using the customer order number.",
                "arguments": ["order_number"],
            },
            {
                "name": "get_products_by_name",
                "description": "Product Search. Search products by name and view essential product information quickly.",
                "arguments": ["product_name"],
            },
            {
                "name": "get_inventory_by_sku",
                "description": "Inventory Lookup. Check real-time inventory availability and stock quantity using product SKU.",
                "arguments": ["sku"],
            },
            {
                "name": "get_customer_by_email",
                "description": "Customer Lookup. Find customer profile, verification status, and addresses using email address.",
                "arguments": ["email"],
            },
            {
                "name": "get_customer_order_history_by_email",
                "description": "Customer Order History. View complete customer order history using the registered email address.",
                "arguments": ["email"],
            },
        ]
