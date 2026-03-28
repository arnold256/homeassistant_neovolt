"""Sensor platform for NeoVolt integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NeoVoltCoordinator


@dataclass(frozen=True, kw_only=True)
class NeoVoltSensorEntityDescription(SensorEntityDescription):
    """Describe a NeoVolt sensor."""

    coordinator_key: str


# All sensor definitions with correct device classes and units for energy dashboard
SENSOR_DESCRIPTIONS: tuple[NeoVoltSensorEntityDescription, ...] = (
    # ── Grid Power ──
    NeoVoltSensorEntityDescription(
        key="total_power_grid",
        coordinator_key="total_power_grid",
        name="Total Power Grid",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── PV Meter Power ──
    NeoVoltSensorEntityDescription(
        key="total_power_pvmeter",
        coordinator_key="total_power_pvmeter",
        name="Total Power PV Meter",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Inverter Power ──
    NeoVoltSensorEntityDescription(
        key="total_power_inverter",
        coordinator_key="total_power_inverter",
        name="Total Power Inverter",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_l1",
        coordinator_key="power_inverter_l1",
        name="Power Inverter L1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_l2",
        coordinator_key="power_inverter_l2",
        name="Power Inverter L2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_l3",
        coordinator_key="power_inverter_l3",
        name="Power Inverter L3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    # ── Inverter Voltage ──
    NeoVoltSensorEntityDescription(
        key="inverter_voltage_l1",
        coordinator_key="inverter_voltage_l1",
        name="Inverter Voltage L1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_voltage_l2",
        coordinator_key="inverter_voltage_l2",
        name="Inverter Voltage L2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_voltage_l3",
        coordinator_key="inverter_voltage_l3",
        name="Inverter Voltage L3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Inverter Misc ──
    NeoVoltSensorEntityDescription(
        key="inverter_temperature",
        coordinator_key="inverter_temperature",
        name="Inverter Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_frequency",
        coordinator_key="grid_frequency",
        name="Grid Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_mode",
        coordinator_key="inverter_mode",
        name="Inverter Mode",
        icon="mdi:information-outline",
    ),
    # ── Inverter Backup ──
    NeoVoltSensorEntityDescription(
        key="power_inverter_backup_total",
        coordinator_key="power_inverter_backup_total",
        name="Power Inverter Backup Total",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_backup_l1",
        coordinator_key="power_inverter_backup_l1",
        name="Power Inverter Backup L1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_backup_l2",
        coordinator_key="power_inverter_backup_l2",
        name="Power Inverter Backup L2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_backup_l3",
        coordinator_key="power_inverter_backup_l3",
        name="Power Inverter Backup L3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    # ── PV Strings ──
    NeoVoltSensorEntityDescription(
        key="power_string_1",
        coordinator_key="power_string_1",
        name="Power PV String 1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="power_string_2",
        coordinator_key="power_string_2",
        name="Power PV String 2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="power_string_3",
        coordinator_key="power_string_3",
        name="Power PV String 3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="power_string_4",
        coordinator_key="power_string_4",
        name="Power PV String 4",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="pv1_voltage",
        coordinator_key="pv1_voltage",
        name="PV1 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="pv1_current",
        coordinator_key="pv1_current",
        name="PV1 Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="pv2_voltage",
        coordinator_key="pv2_voltage",
        name="PV2 Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="pv2_current",
        coordinator_key="pv2_current",
        name="PV2 Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Energy Statistics (for Energy Dashboard) ──
    NeoVoltSensorEntityDescription(
        key="energy_feed_to_grid",
        coordinator_key="energy_feed_to_grid",
        name="Total Energy Feed to Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_consumption_from_grid",
        coordinator_key="energy_consumption_from_grid",
        name="Total Energy Consumption from Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_feed_to_grid_pvmeter",
        coordinator_key="energy_feed_to_grid_pvmeter",
        name="Total Energy Feed to Grid (PV Meter)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_consumption_from_grid_pvmeter",
        coordinator_key="energy_consumption_from_grid_pvmeter",
        name="Total Energy Consumption from Grid (PV Meter)",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_charge_battery",
        coordinator_key="energy_charge_battery",
        name="Total Energy Charge Battery",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_discharge_battery",
        coordinator_key="energy_discharge_battery",
        name="Total Energy Discharge Battery",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_charge_battery_from_grid",
        coordinator_key="energy_charge_battery_from_grid",
        name="Total Energy Charge Battery from Grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_from_pv",
        coordinator_key="energy_from_pv",
        name="Total Energy from PV",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # ── Battery ──
    NeoVoltSensorEntityDescription(
        key="battery_soc",
        coordinator_key="battery_soc",
        name="Battery State of Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_voltage",
        coordinator_key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_current",
        coordinator_key="battery_current",
        name="Battery Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_power",
        coordinator_key="battery_power",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_min_cell_temp",
        coordinator_key="battery_min_cell_temp",
        name="Battery Min Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_max_cell_temp",
        coordinator_key="battery_max_cell_temp",
        name="Battery Max Cell Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_max_charge_current",
        coordinator_key="battery_max_charge_current",
        name="Battery Max Charge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_max_discharge_current",
        coordinator_key="battery_max_discharge_current",
        name="Battery Max Discharge Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_remaining_time",
        coordinator_key="battery_remaining_time",
        name="Battery Remaining Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
    ),
    NeoVoltSensorEntityDescription(
        key="battery_relay_status",
        coordinator_key="battery_relay_status",
        name="Battery Relay Status",
        icon="mdi:electric-switch",
    ),
    NeoVoltSensorEntityDescription(
        key="battery_ups_soc",
        coordinator_key="battery_ups_soc",
        name="UPS SOC Reserve",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="max_feed_to_grid",
        coordinator_key="max_feed_to_grid",
        name="Max Feed to Grid",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:transmission-tower-export",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Grid Voltages ──
    NeoVoltSensorEntityDescription(
        key="grid_voltage_phase_a",
        coordinator_key="grid_voltage_phase_a",
        name="Grid Voltage Phase A",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_voltage_phase_b",
        coordinator_key="grid_voltage_phase_b",
        name="Grid Voltage Phase B",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_voltage_phase_c",
        coordinator_key="grid_voltage_phase_c",
        name="Grid Voltage Phase C",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Faults ──
    NeoVoltSensorEntityDescription(
        key="inverter_fault_1",
        coordinator_key="inverter_fault_1",
        name="Inverter Fault 1",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_fault_2",
        coordinator_key="inverter_fault_2",
        name="Inverter Fault 2",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_extended_fault_1",
        coordinator_key="inverter_extended_fault_1",
        name="Inverter Extended Fault 1",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_extended_fault_2",
        coordinator_key="inverter_extended_fault_2",
        name="Inverter Extended Fault 2",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="system_fault",
        coordinator_key="system_fault",
        name="System Fault",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    # ── EMS Versions ──
    NeoVoltSensorEntityDescription(
        key="ems_version_high",
        coordinator_key="ems_version_high",
        name="EMS Version High",
        icon="mdi:numeric",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="ems_version_middle",
        coordinator_key="ems_version_middle",
        name="EMS Version Middle",
        icon="mdi:numeric",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="ems_version_low",
        coordinator_key="ems_version_low",
        name="EMS Version Low",
        icon="mdi:numeric",
        entity_registry_enabled_default=False,
    ),
    # ── CT Rates ──
    NeoVoltSensorEntityDescription(
        key="gridmeter_ct_rate",
        coordinator_key="gridmeter_ct_rate",
        name="Grid Meter CT Rate",
        icon="mdi:meter-electric-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="pvmeter_ct_rate",
        coordinator_key="pvmeter_ct_rate",
        name="PV Meter CT Rate",
        icon="mdi:meter-electric-outline",
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NeoVolt sensor entities."""
    coordinator: NeoVoltCoordinator = entry.runtime_data

    async_add_entities(
        NeoVoltSensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    )


class NeoVoltSensor(CoordinatorEntity[NeoVoltCoordinator], SensorEntity):
    """Representation of a NeoVolt sensor."""

    entity_description: NeoVoltSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NeoVoltCoordinator,
        description: NeoVoltSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> float | int | None:
        """Return the sensor value."""
        return self.coordinator.data.get(self.entity_description.coordinator_key)
