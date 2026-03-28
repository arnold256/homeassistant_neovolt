"""Sensor platform for NeoVolt integration."""

from __future__ import annotations

from dataclasses import dataclass, field

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

from .const import (
    BATTERY_RELAY_STATUS_MAP,
    BATTERY_STATUS_MAP,
    DOMAIN,
    INVERTER_MODE_MAP,
)
from .coordinator import NeoVoltCoordinator


@dataclass(frozen=True, kw_only=True)
class NeoVoltSensorEntityDescription(SensorEntityDescription):
    """Describe a NeoVolt sensor."""

    coordinator_key: str
    value_map: dict[int, str] = field(default_factory=dict)


SENSOR_DESCRIPTIONS: tuple[NeoVoltSensorEntityDescription, ...] = (
    # ── Grid Meter ──
    NeoVoltSensorEntityDescription(
        key="total_power_grid",
        coordinator_key="total_power_grid",
        translation_key="total_power_grid",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_power_phase_a",
        coordinator_key="grid_power_phase_a",
        translation_key="grid_power_phase_a",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_power_phase_b",
        coordinator_key="grid_power_phase_b",
        translation_key="grid_power_phase_b",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_power_phase_c",
        coordinator_key="grid_power_phase_c",
        translation_key="grid_power_phase_c",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_voltage_phase_a",
        coordinator_key="grid_voltage_phase_a",
        translation_key="grid_voltage_phase_a",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_voltage_phase_b",
        coordinator_key="grid_voltage_phase_b",
        translation_key="grid_voltage_phase_b",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_voltage_phase_c",
        coordinator_key="grid_voltage_phase_c",
        translation_key="grid_voltage_phase_c",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_current_phase_a",
        coordinator_key="grid_current_phase_a",
        translation_key="grid_current_phase_a",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_current_phase_b",
        coordinator_key="grid_current_phase_b",
        translation_key="grid_current_phase_b",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_current_phase_c",
        coordinator_key="grid_current_phase_c",
        translation_key="grid_current_phase_c",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_frequency_meter",
        coordinator_key="grid_frequency_meter",
        translation_key="grid_frequency_meter",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    # ── PV Meter ──
    NeoVoltSensorEntityDescription(
        key="total_power_pvmeter",
        coordinator_key="total_power_pvmeter",
        translation_key="total_power_pvmeter",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Inverter Power ──
    NeoVoltSensorEntityDescription(
        key="total_power_inverter",
        coordinator_key="total_power_inverter",
        translation_key="total_power_inverter",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_l1",
        coordinator_key="power_inverter_l1",
        translation_key="power_inverter_l1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_l2",
        coordinator_key="power_inverter_l2",
        translation_key="power_inverter_l2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_l3",
        coordinator_key="power_inverter_l3",
        translation_key="power_inverter_l3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    # ── Inverter Voltage ──
    NeoVoltSensorEntityDescription(
        key="inverter_voltage_l1",
        coordinator_key="inverter_voltage_l1",
        translation_key="inverter_voltage_l1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_voltage_l2",
        coordinator_key="inverter_voltage_l2",
        translation_key="inverter_voltage_l2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_voltage_l3",
        coordinator_key="inverter_voltage_l3",
        translation_key="inverter_voltage_l3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Inverter Current ──
    NeoVoltSensorEntityDescription(
        key="inverter_current_l1",
        coordinator_key="inverter_current_l1",
        translation_key="inverter_current_l1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_current_l2",
        coordinator_key="inverter_current_l2",
        translation_key="inverter_current_l2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_current_l3",
        coordinator_key="inverter_current_l3",
        translation_key="inverter_current_l3",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    # ── Inverter Misc ──
    NeoVoltSensorEntityDescription(
        key="inverter_temperature",
        coordinator_key="inverter_temperature",
        translation_key="inverter_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="grid_frequency",
        coordinator_key="grid_frequency",
        translation_key="grid_frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_mode",
        coordinator_key="inverter_mode",
        translation_key="inverter_mode",
        icon="mdi:information-outline",
        value_map=INVERTER_MODE_MAP,
    ),
    # ── Inverter Backup ──
    NeoVoltSensorEntityDescription(
        key="power_inverter_backup_total",
        coordinator_key="power_inverter_backup_total",
        translation_key="power_inverter_backup_total",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_backup_l1",
        coordinator_key="power_inverter_backup_l1",
        translation_key="power_inverter_backup_l1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_backup_l2",
        coordinator_key="power_inverter_backup_l2",
        translation_key="power_inverter_backup_l2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="power_inverter_backup_l3",
        coordinator_key="power_inverter_backup_l3",
        translation_key="power_inverter_backup_l3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    # ── PV Strings ──
    NeoVoltSensorEntityDescription(
        key="power_string_1",
        coordinator_key="power_string_1",
        translation_key="power_string_1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="power_string_2",
        coordinator_key="power_string_2",
        translation_key="power_string_2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="power_string_3",
        coordinator_key="power_string_3",
        translation_key="power_string_3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="power_string_4",
        coordinator_key="power_string_4",
        translation_key="power_string_4",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="pv1_voltage",
        coordinator_key="pv1_voltage",
        translation_key="pv1_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="pv1_current",
        coordinator_key="pv1_current",
        translation_key="pv1_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="pv2_voltage",
        coordinator_key="pv2_voltage",
        translation_key="pv2_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="pv2_current",
        coordinator_key="pv2_current",
        translation_key="pv2_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="pv3_voltage",
        coordinator_key="pv3_voltage",
        translation_key="pv3_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="pv3_current",
        coordinator_key="pv3_current",
        translation_key="pv3_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="pv4_voltage",
        coordinator_key="pv4_voltage",
        translation_key="pv4_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="pv4_current",
        coordinator_key="pv4_current",
        translation_key="pv4_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    # ── Energy Statistics (Energy Dashboard) ──
    NeoVoltSensorEntityDescription(
        key="energy_feed_to_grid",
        coordinator_key="energy_feed_to_grid",
        translation_key="energy_feed_to_grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_consumption_from_grid",
        coordinator_key="energy_consumption_from_grid",
        translation_key="energy_consumption_from_grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_feed_to_grid_pvmeter",
        coordinator_key="energy_feed_to_grid_pvmeter",
        translation_key="energy_feed_to_grid_pvmeter",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_consumption_from_grid_pvmeter",
        coordinator_key="energy_consumption_from_grid_pvmeter",
        translation_key="energy_consumption_from_grid_pvmeter",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_charge_battery",
        coordinator_key="energy_charge_battery",
        translation_key="energy_charge_battery",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_discharge_battery",
        coordinator_key="energy_discharge_battery",
        translation_key="energy_discharge_battery",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_charge_battery_from_grid",
        coordinator_key="energy_charge_battery_from_grid",
        translation_key="energy_charge_battery_from_grid",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="energy_from_pv",
        coordinator_key="energy_from_pv",
        translation_key="energy_from_pv",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    NeoVoltSensorEntityDescription(
        key="pv_inverter_energy",
        coordinator_key="pv_inverter_energy",
        translation_key="pv_inverter_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="system_total_pv_energy",
        coordinator_key="system_total_pv_energy",
        translation_key="system_total_pv_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    # ── Battery ──
    NeoVoltSensorEntityDescription(
        key="battery_soc",
        coordinator_key="battery_soc",
        translation_key="battery_soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_soh",
        coordinator_key="battery_soh",
        translation_key="battery_soh",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:heart-pulse",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_voltage",
        coordinator_key="battery_voltage",
        translation_key="battery_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_current",
        coordinator_key="battery_current",
        translation_key="battery_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_power",
        coordinator_key="battery_power",
        translation_key="battery_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_min_cell_temp",
        coordinator_key="battery_min_cell_temp",
        translation_key="battery_min_cell_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_max_cell_temp",
        coordinator_key="battery_max_cell_temp",
        translation_key="battery_max_cell_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_max_charge_current",
        coordinator_key="battery_max_charge_current",
        translation_key="battery_max_charge_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_max_discharge_current",
        coordinator_key="battery_max_discharge_current",
        translation_key="battery_max_discharge_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_max_charge_power",
        coordinator_key="battery_max_charge_power",
        translation_key="battery_max_charge_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_max_discharge_power",
        coordinator_key="battery_max_discharge_power",
        translation_key="battery_max_discharge_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_capacity",
        coordinator_key="battery_capacity",
        translation_key="battery_capacity",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:battery-high",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_remaining_time",
        coordinator_key="battery_remaining_time",
        translation_key="battery_remaining_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
    ),
    NeoVoltSensorEntityDescription(
        key="battery_status",
        coordinator_key="battery_status",
        translation_key="battery_status",
        icon="mdi:battery-check-outline",
        value_map=BATTERY_STATUS_MAP,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_relay_status",
        coordinator_key="battery_relay_status",
        translation_key="battery_relay_status",
        icon="mdi:electric-switch",
        value_map=BATTERY_RELAY_STATUS_MAP,
    ),
    NeoVoltSensorEntityDescription(
        key="battery_ups_soc",
        coordinator_key="battery_ups_soc",
        translation_key="battery_ups_soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NeoVoltSensorEntityDescription(
        key="max_feed_to_grid",
        coordinator_key="max_feed_to_grid",
        translation_key="max_feed_to_grid",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:transmission-tower-export",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Faults & Warnings ──
    NeoVoltSensorEntityDescription(
        key="inverter_fault_1",
        coordinator_key="inverter_fault_1",
        translation_key="inverter_fault_1",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_fault_2",
        coordinator_key="inverter_fault_2",
        translation_key="inverter_fault_2",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_warning_1",
        coordinator_key="inverter_warning_1",
        translation_key="inverter_warning_1",
        icon="mdi:alert-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_warning_2",
        coordinator_key="inverter_warning_2",
        translation_key="inverter_warning_2",
        icon="mdi:alert-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_extended_fault_1",
        coordinator_key="inverter_extended_fault_1",
        translation_key="inverter_extended_fault_1",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_extended_fault_2",
        coordinator_key="inverter_extended_fault_2",
        translation_key="inverter_extended_fault_2",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="system_fault",
        coordinator_key="system_fault",
        translation_key="system_fault",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=False,
    ),
    # ── EMS Versions ──
    NeoVoltSensorEntityDescription(
        key="ems_version_high",
        coordinator_key="ems_version_high",
        translation_key="ems_version_high",
        icon="mdi:numeric",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="ems_version_middle",
        coordinator_key="ems_version_middle",
        translation_key="ems_version_middle",
        icon="mdi:numeric",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="ems_version_low",
        coordinator_key="ems_version_low",
        translation_key="ems_version_low",
        icon="mdi:numeric",
        entity_registry_enabled_default=False,
    ),
    # ── CT Rates ──
    NeoVoltSensorEntityDescription(
        key="gridmeter_ct_rate",
        coordinator_key="gridmeter_ct_rate",
        translation_key="gridmeter_ct_rate",
        icon="mdi:meter-electric-outline",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="pvmeter_ct_rate",
        coordinator_key="pvmeter_ct_rate",
        translation_key="pvmeter_ct_rate",
        icon="mdi:meter-electric-outline",
        entity_registry_enabled_default=False,
    ),
    # ── Inverter Info ──
    NeoVoltSensorEntityDescription(
        key="inverter_master_version",
        coordinator_key="inverter_master_version",
        translation_key="inverter_master_version",
        icon="mdi:chip",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_slave_version",
        coordinator_key="inverter_slave_version",
        translation_key="inverter_slave_version",
        icon="mdi:chip",
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="inverter_serial_number",
        coordinator_key="inverter_serial_number",
        translation_key="inverter_serial_number",
        icon="mdi:identifier",
        entity_registry_enabled_default=False,
    ),
    # ── Dispatch read-back ──
    NeoVoltSensorEntityDescription(
        key="dispatch_active_power",
        coordinator_key="dispatch_active_power",
        translation_key="dispatch_active_power_sensor",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="dispatch_reactive_power",
        coordinator_key="dispatch_reactive_power",
        translation_key="dispatch_reactive_power_sensor",
        native_unit_of_measurement="var",
        icon="mdi:sine-wave",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="dispatch_soc",
        coordinator_key="dispatch_soc",
        translation_key="dispatch_soc_sensor",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:battery-sync-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    NeoVoltSensorEntityDescription(
        key="dispatch_time",
        coordinator_key="dispatch_time",
        translation_key="dispatch_time_sensor",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
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
    def native_value(self) -> float | int | str | None:
        """Return the sensor value, mapped to a label for status sensors."""
        raw = self.coordinator.data.get(self.entity_description.coordinator_key)
        if raw is None:
            return None
        if self.entity_description.value_map:
            return self.entity_description.value_map.get(int(raw), f"Unknown ({raw})")
        return raw
