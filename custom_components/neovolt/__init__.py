"""The NeoVolt (AlphaESS Modbus) integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SCAN_INTERVAL, CONF_SLAVE_ID, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import NeoVoltCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]

type NeoVoltConfigEntry = ConfigEntry[NeoVoltCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: NeoVoltConfigEntry) -> bool:
    """Set up NeoVolt from a config entry."""
    coordinator = NeoVoltCoordinator(
        hass,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        slave_id=entry.data[CONF_SLAVE_ID],
        scan_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: NeoVoltConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: NeoVoltCoordinator = entry.runtime_data
        await coordinator.async_shutdown()

    return unload_ok
