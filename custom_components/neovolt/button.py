"""Button platform for NeoVolt integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NeoVoltCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NeoVolt button entities."""
    coordinator: NeoVoltCoordinator = entry.runtime_data

    async_add_entities([
        NeoVoltDispatchStartButton(coordinator, entry),
        NeoVoltDispatchStopButton(coordinator, entry),
    ])


class NeoVoltDispatchStartButton(CoordinatorEntity[NeoVoltCoordinator], ButtonEntity):
    """Button to start dispatch with current parameter values.

    Writes all dispatch registers in the required sequence
    (Dispatch Mode must be written last).
    """

    _attr_has_entity_name = True
    _attr_translation_key = "dispatch_start_button"
    _attr_icon = "mdi:play-circle"

    def __init__(
        self,
        coordinator: NeoVoltCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_dispatch_start_button"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="AlphaESS",
            model="Smile Hi10",
            configuration_url=f"http://{entry.data[CONF_HOST]}",
        )

    async def async_press(self) -> None:
        """Start dispatch using current register values."""
        data = self.coordinator.data

        # Read current dispatch parameter values
        active_power = int(data.get("dispatch_active_power", 0))
        reactive_power = int(data.get("dispatch_reactive_power", 0))
        mode = int(data.get("dispatch_mode", 2))
        soc_pct = float(data.get("dispatch_soc", 0) or 0)
        duration = int(data.get("dispatch_time", 3600))

        await self.coordinator.async_dispatch_start(
            active_power_w=active_power,
            duration_s=duration,
            mode=mode,
            soc_pct=soc_pct,
            reactive_power_var=reactive_power,
        )


class NeoVoltDispatchStopButton(CoordinatorEntity[NeoVoltCoordinator], ButtonEntity):
    """Button to stop dispatch mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "dispatch_stop_button"
    _attr_icon = "mdi:stop-circle"

    def __init__(
        self,
        coordinator: NeoVoltCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_dispatch_stop_button"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="AlphaESS",
            model="Smile Hi10",
            configuration_url=f"http://{entry.data[CONF_HOST]}",
        )

    async def async_press(self) -> None:
        """Stop dispatch."""
        await self.coordinator.async_dispatch_stop()
