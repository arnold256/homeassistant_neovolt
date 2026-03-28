"""Config flow for NeoVolt integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from pymodbus.client import AsyncModbusTcpClient

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class NeoVoltConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NeoVolt."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            slave_id = user_input[CONF_SLAVE_ID]

            # Check if already configured with same host
            self._async_abort_entries_match({CONF_HOST: host})

            # Test connection
            client = AsyncModbusTcpClient(host=host, port=port, timeout=5)
            try:
                await client.connect()
                if not client.connected:
                    errors["base"] = "cannot_connect"
                else:
                    result = await client.read_holding_registers(
                        address=258, count=1, slave=slave_id
                    )
                    if result.isError():
                        errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Error connecting to NeoVolt device")
                errors["base"] = "cannot_connect"
            finally:
                client.close()

            if not errors:
                return self.async_create_entry(
                    title=f"NeoVolt ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_SLAVE_ID: slave_id,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(int, vol.Range(min=5, max=300)),
                }
            ),
            errors=errors,
        )
