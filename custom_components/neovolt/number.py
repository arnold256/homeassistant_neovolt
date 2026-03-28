"""Number platform for NeoVolt integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NeoVoltCoordinator


@dataclass(frozen=True, kw_only=True)
class NeoVoltNumberEntityDescription(NumberEntityDescription):
    """Describe a NeoVolt number entity."""

    register_address: int
    coordinator_key: str


NUMBER_DESCRIPTIONS: tuple[NeoVoltNumberEntityDescription, ...] = (
    NeoVoltNumberEntityDescription(
        key="target_soc",
        coordinator_key="battery_ups_soc",
        name="Target SOC",
        icon="mdi:battery-charging",
        native_min_value=4,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        register_address=2128,
    ),
    NeoVoltNumberEntityDescription(
        key="max_feed_to_grid",
        coordinator_key="max_feed_to_grid",
        name="Max Feed to Grid Rate",
        icon="mdi:transmission-tower-export",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        register_address=2048,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NeoVolt number entities."""
    coordinator: NeoVoltCoordinator = entry.runtime_data

    async_add_entities(
        NeoVoltNumber(coordinator, description, entry)
        for description in NUMBER_DESCRIPTIONS
    )


class NeoVoltNumber(CoordinatorEntity[NeoVoltCoordinator], NumberEntity):
    """Representation of a NeoVolt number entity (writable register)."""

    entity_description: NeoVoltNumberEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NeoVoltCoordinator,
        description: NeoVoltNumberEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="AlphaESS",
            model="Smile Hi10",
            configuration_url=f"http://{entry.data[CONF_HOST]}",
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value from the coordinator."""
        val = self.coordinator.data.get(self.entity_description.coordinator_key)
        if val is not None:
            return float(val)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Write the value to the Modbus register."""
        await self.coordinator.async_write_register(
            address=self.entity_description.register_address,
            value=int(value),
        )
        await self.coordinator.async_request_refresh()
