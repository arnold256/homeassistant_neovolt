"""Number platform for NeoVolt integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, PERCENTAGE, UnitOfPower, UnitOfTime
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
    write_scale: float = 1.0
    register_count: int = 1  # 1 for 16-bit, 2 for 32-bit writes


NUMBER_DESCRIPTIONS: tuple[NeoVoltNumberEntityDescription, ...] = (
    # ── Existing controls ──
    NeoVoltNumberEntityDescription(
        key="target_soc",
        coordinator_key="battery_ups_soc",
        translation_key="target_soc",
        icon="mdi:battery-charging",
        native_min_value=4,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        register_address=2128,
    ),
    NeoVoltNumberEntityDescription(
        key="max_feed_to_grid_control",
        coordinator_key="max_feed_to_grid",
        translation_key="max_feed_to_grid_control",
        icon="mdi:transmission-tower-export",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        register_address=2048,
    ),
    # ── Charge Cut SOC ──
    NeoVoltNumberEntityDescription(
        key="charge_cut_soc",
        coordinator_key="charge_cut_soc",
        translation_key="charge_cut_soc",
        icon="mdi:battery-lock",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        register_address=2133,
        write_scale=10,  # register scale 0.1 → 50% writes 500
    ),
    # ── Discharge time slots ──
    NeoVoltNumberEntityDescription(
        key="discharge_start_time_1",
        coordinator_key="discharge_start_time_1",
        translation_key="discharge_start_time_1",
        icon="mdi:clock-start",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        mode=NumberMode.BOX,
        register_address=2129,
    ),
    NeoVoltNumberEntityDescription(
        key="discharge_stop_time_1",
        coordinator_key="discharge_stop_time_1",
        translation_key="discharge_stop_time_1",
        icon="mdi:clock-end",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        mode=NumberMode.BOX,
        register_address=2130,
    ),
    NeoVoltNumberEntityDescription(
        key="discharge_start_time_2",
        coordinator_key="discharge_start_time_2",
        translation_key="discharge_start_time_2",
        icon="mdi:clock-start",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        mode=NumberMode.BOX,
        register_address=2131,
        entity_registry_enabled_default=False,
    ),
    NeoVoltNumberEntityDescription(
        key="discharge_stop_time_2",
        coordinator_key="discharge_stop_time_2",
        translation_key="discharge_stop_time_2",
        icon="mdi:clock-end",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        mode=NumberMode.BOX,
        register_address=2132,
        entity_registry_enabled_default=False,
    ),
    # ── Charge time slots ──
    NeoVoltNumberEntityDescription(
        key="charge_start_time_1",
        coordinator_key="charge_start_time_1",
        translation_key="charge_start_time_1",
        icon="mdi:clock-start",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        mode=NumberMode.BOX,
        register_address=2134,
    ),
    NeoVoltNumberEntityDescription(
        key="charge_stop_time_1",
        coordinator_key="charge_stop_time_1",
        translation_key="charge_stop_time_1",
        icon="mdi:clock-end",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        mode=NumberMode.BOX,
        register_address=2135,
    ),
    NeoVoltNumberEntityDescription(
        key="charge_start_time_2",
        coordinator_key="charge_start_time_2",
        translation_key="charge_start_time_2",
        icon="mdi:clock-start",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        mode=NumberMode.BOX,
        register_address=2136,
        entity_registry_enabled_default=False,
    ),
    NeoVoltNumberEntityDescription(
        key="charge_stop_time_2",
        coordinator_key="charge_stop_time_2",
        translation_key="charge_stop_time_2",
        icon="mdi:clock-end",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        mode=NumberMode.BOX,
        register_address=2137,
        entity_registry_enabled_default=False,
    ),
    # ── Dispatch controls ──
    NeoVoltNumberEntityDescription(
        key="dispatch_active_power_control",
        coordinator_key="dispatch_active_power",
        translation_key="dispatch_active_power",
        icon="mdi:flash",
        native_min_value=-30000,
        native_max_value=30000,
        native_step=100,
        native_unit_of_measurement=UnitOfPower.WATT,
        mode=NumberMode.BOX,
        register_address=2177,
        register_count=2,
        entity_registry_enabled_default=False,
    ),
    NeoVoltNumberEntityDescription(
        key="dispatch_reactive_power_control",
        coordinator_key="dispatch_reactive_power",
        translation_key="dispatch_reactive_power",
        icon="mdi:sine-wave",
        native_min_value=-30000,
        native_max_value=30000,
        native_step=100,
        native_unit_of_measurement="var",
        mode=NumberMode.BOX,
        register_address=2179,
        register_count=2,
        entity_registry_enabled_default=False,
    ),
    NeoVoltNumberEntityDescription(
        key="dispatch_soc_control",
        coordinator_key="dispatch_soc",
        translation_key="dispatch_soc",
        icon="mdi:battery-sync-outline",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        register_address=2182,
        write_scale=2.5,  # register scale 0.4 → 50% writes 125
        entity_registry_enabled_default=False,
    ),
    NeoVoltNumberEntityDescription(
        key="dispatch_time_control",
        coordinator_key="dispatch_time",
        translation_key="dispatch_time",
        icon="mdi:timer-outline",
        native_min_value=0,
        native_max_value=86400,
        native_step=60,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        mode=NumberMode.BOX,
        register_address=2183,
        register_count=2,
        entity_registry_enabled_default=False,
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
        """Write the value to Modbus register(s)."""
        raw = int(value * self.entity_description.write_scale)
        desc = self.entity_description

        if desc.register_count == 2:
            # 32-bit write: split into high and low 16-bit words
            if raw < 0:
                raw = raw + 0x100000000  # convert to unsigned 32-bit
            high = (raw >> 16) & 0xFFFF
            low = raw & 0xFFFF
            await self.coordinator.async_write_registers(
                desc.register_address, [high, low]
            )
        else:
            await self.coordinator.async_write_register(
                desc.register_address, raw
            )

        await self.coordinator.async_request_refresh()
