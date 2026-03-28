"""Select platform for NeoVolt integration."""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BATTERY_MOS_CONTROL_OPTIONS,
    BATTERY_RELAY_STATUS_MAP,
    DISPATCH_MODE_MAP,
    DISPATCH_START_MAP,
    DOMAIN,
    TIME_PERIOD_CONTROL_MAP,
)
from .coordinator import NeoVoltCoordinator


@dataclass(frozen=True, kw_only=True)
class NeoVoltSelectEntityDescription(SelectEntityDescription):
    """Describe a NeoVolt select entity."""

    register_address: int
    coordinator_key: str
    options_map: dict[int, str] = field(default_factory=dict)
    # read_map includes all possible values for display (superset of options_map)
    read_map: dict[int, str] = field(default_factory=dict)


SELECT_DESCRIPTIONS: tuple[NeoVoltSelectEntityDescription, ...] = (
    NeoVoltSelectEntityDescription(
        key="battery_mos_control",
        coordinator_key="battery_mos_control",
        translation_key="battery_mos_control",
        icon="mdi:electric-switch",
        options=list(BATTERY_MOS_CONTROL_OPTIONS.values()),
        options_map=BATTERY_MOS_CONTROL_OPTIONS,
        read_map=BATTERY_RELAY_STATUS_MAP,  # includes 0=Disconnected for display
        register_address=302,
    ),
    NeoVoltSelectEntityDescription(
        key="time_period_control_flag",
        coordinator_key="time_period_control_flag",
        translation_key="time_period_control_flag",
        icon="mdi:calendar-clock",
        options=list(TIME_PERIOD_CONTROL_MAP.values()),
        options_map=TIME_PERIOD_CONTROL_MAP,
        register_address=2127,
    ),
    NeoVoltSelectEntityDescription(
        key="dispatch_start",
        coordinator_key="dispatch_start",
        translation_key="dispatch_start",
        icon="mdi:play-circle-outline",
        options=list(DISPATCH_START_MAP.values()),
        options_map=DISPATCH_START_MAP,
        register_address=2176,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSelectEntityDescription(
        key="dispatch_mode",
        coordinator_key="dispatch_mode",
        translation_key="dispatch_mode",
        icon="mdi:cog-outline",
        options=list(DISPATCH_MODE_MAP.values()),
        options_map=DISPATCH_MODE_MAP,
        register_address=2181,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NeoVolt select entities."""
    coordinator: NeoVoltCoordinator = entry.runtime_data

    async_add_entities(
        NeoVoltSelect(coordinator, description, entry)
        for description in SELECT_DESCRIPTIONS
    )


class NeoVoltSelect(CoordinatorEntity[NeoVoltCoordinator], SelectEntity):
    """Representation of a NeoVolt select entity (writable lookup register)."""

    entity_description: NeoVoltSelectEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NeoVoltCoordinator,
        description: NeoVoltSelectEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
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
        # Build reverse map: label → register value (writable options only)
        self._label_to_value = {v: k for k, v in description.options_map.items()}
        # For reading: use read_map if provided, otherwise fall back to options_map
        self._display_map = description.read_map or description.options_map

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        raw = self.coordinator.data.get(self.entity_description.coordinator_key)
        if raw is None:
            return None
        return self._display_map.get(int(raw))

    async def async_select_option(self, option: str) -> None:
        """Write the selected option to the Modbus register."""
        value = self._label_to_value.get(option)
        if value is None:
            return
        await self.coordinator.async_write_register(
            self.entity_description.register_address, value
        )
        await self.coordinator.async_request_refresh()
