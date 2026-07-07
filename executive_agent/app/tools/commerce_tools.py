"""Commercetools-backed business tools for the agent workflow."""

from app.config import constants
from app.config.settings import Settings, get_settings
from app.models.errors import CommerceToolsError
from app.services.commercetools_client import CommerceToolsClient
from app.tools.normalizers import (
    normalize_customer,
    normalize_customer_order_history,
    normalize_inventory,
    normalize_order,
    normalize_product_projection,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CommerceTools:
    """Business capabilities backed by one or more commercetools REST calls."""

    def __init__(self, client: CommerceToolsClient | None = None, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = client or CommerceToolsClient(self.settings)

    async def get_order_by_order_number(self, order_number: str) -> dict:
        """Retrieve and normalize one order by order number."""

        path = constants.ORDER_BY_NUMBER_PATH.format(
            project_key=self.settings.ctp_project_key,
            order_number=self.client.encode_path_value(order_number),
        )
        logger.info("tool=get_order_by_order_number order_number=%s", order_number)
        payload = await self.client.get(path)
        return normalize_order(payload)

    async def get_products_by_name(self, product_name: str) -> list[dict]:
        """Search product projections by English product name."""

        path = constants.PRODUCT_PROJECTIONS_SEARCH_PATH.format(project_key=self.settings.ctp_project_key)
        logger.info("tool=get_products_by_name product_name=%s", product_name)
        payload = await self.client.get(path, params={"text.en-US": product_name})
        return [normalize_product_projection(product) for product in payload.get("results", [])]

    async def get_inventory_by_sku(self, sku: str) -> dict:
        """Retrieve inventory information for a SKU."""

        path = constants.INVENTORY_PATH.format(project_key=self.settings.ctp_project_key)
        logger.info("tool=get_inventory_by_sku sku=%s", sku)
        payload = await self.client.get(path, params={"where": f'sku="{sku}"'})
        if not payload.get("results"):
            raise CommerceToolsError("INVENTORY_NOT_FOUND", f"Inventory for SKU {sku} could not be found.", "get_inventory_by_sku")
        return normalize_inventory(payload)

    async def get_customer_by_email(self, email: str) -> dict:
        """Retrieve customer details by email address."""

        path = constants.CUSTOMERS_PATH.format(project_key=self.settings.ctp_project_key)
        logger.info("tool=get_customer_by_email email=%s", email)
        payload = await self.client.get(path, params={"where": f'email="{email}"'})
        results = payload.get("results") or []
        if not results:
            raise CommerceToolsError("CUSTOMER_NOT_FOUND", f"Customer {email} could not be found.", "get_customer_by_email")
        return normalize_customer(results[0])

    async def get_customer_order_history_by_email(self, email: str) -> dict:
        """Retrieve a customer and then all orders for that customer."""

        logger.info("tool=get_customer_order_history_by_email email=%s", email)
        customer = await self.get_customer_by_email(email)
        customer_id = customer["customerId"]
        path = constants.ORDERS_PATH.format(project_key=self.settings.ctp_project_key)
        payload = await self.client.get(path, params={"where": f'customerId="{customer_id}"'})
        return normalize_customer_order_history(email, payload)
