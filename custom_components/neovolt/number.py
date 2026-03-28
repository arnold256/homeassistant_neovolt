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
    read_scale: float = 1.0  # scale factor to convert raw register → display value
    read_dtype: str = "u16"  # data type for readback decoding
    is_offset_32000: bool = False  # dispatch power uses offset encoding


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
        read_scale=1,
        read_dtype="u16",
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
        read_scale=1,
        read_dtype="u16",
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
        read_scale=0.1,
        read_dtype="u16",
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
    ),
    # ── Dispatch controls ──
    # Active/Reactive power use offset-32000 encoding in the register.
    # UI shows signed watts (negative=charge, positive=discharge).
    # Write: register = 32000 + user_value. Read: user_value = register - 32000.
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
        read_scale=1,
        read_dtype="u32",  # unsigned with offset, not signed
        is_offset_32000=True,
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
        read_scale=1,
        read_dtype="u32",  # unsigned with offset, not signed
        is_offset_32000=True,
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
        read_scale=0.4,
        read_dtype="u16",
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
        read_scale=1,
        read_dtype="u32",
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
        """Write the value to Modbus register(s) and immediately read back."""
        raw = int(value * self.entity_description.write_scale)
        desc = self.entity_description

        if desc.is_offset_32000:
            # Dispatch power: user value is signed watts, register uses offset 32000
            # -2000W (charge) → register 30000, +2000W (discharge) → register 34000
            register_val = 32000 + raw
            high = (register_val >> 16) & 0xFFFF
            low = register_val & 0xFFFF
            await self.coordinator.async_write_and_readback_32(
                desc.register_address,
                [high, low],
                desc.coordinator_key,
                desc.read_scale,
                desc.read_dtype,
            )
            # Override coordinator data with the offset-adjusted display value
            self.coordinator.data[desc.coordinator_key] = raw
        elif desc.register_count == 2:
            # 32-bit write (unsigned, e.g. dispatch_time)
            high = (raw >> 16) & 0xFFFF
            low = raw & 0xFFFF
            await self.coordinator.async_write_and_readback_32(
                desc.register_address,
                [high, low],
                desc.coordinator_key,
                desc.read_scale,
                desc.read_dtype,
            )
        else:
            await self.coordinator.async_write_and_readback(
                desc.register_address,
                raw,
                desc.coordinator_key,
                desc.read_scale,
                desc.read_dtype,
            )

        self.async_write_ha_state()
