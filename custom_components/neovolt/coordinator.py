"""DataUpdateCoordinator for NeoVolt integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class NeoVoltCoordinator(DataUpdateCoordinator[dict[str, float | int | None]]):
    """Coordinator to poll Modbus registers from AlphaESS inverter."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        slave_id: int,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"NeoVolt ({host})",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self._client: AsyncModbusTcpClient | None = None

    async def _ensure_connected(self) -> AsyncModbusTcpClient:
        """Ensure we have an active Modbus connection."""
        if self._client is None or not self._client.connected:
            self._client = AsyncModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=10,
            )
            await self._client.connect()
            if not self._client.connected:
                raise UpdateFailed(f"Cannot connect to {self.host}:{self.port}")
        return self._client

    async def _read_register(
        self,
        client: AsyncModbusTcpClient,
        address: int,
        count: int = 2,
    ) -> list[int] | None:
        """Read holding registers, return raw register values or None."""
        try:
            result = await client.read_holding_registers(
                address=address,
                count=count,
                slave=self.slave_id,
            )
            if result.isError():
                _LOGGER.debug("Error reading register %s: %s", address, result)
                return None
            return list(result.registers)
        except (ModbusException, AttributeError) as err:
            _LOGGER.debug("Exception reading register %s: %s", address, err)
            return None

    @staticmethod
    def _decode_int16(registers: list[int]) -> int:
        """Decode a signed 16-bit value from a single register."""
        val = registers[0]
        if val >= 0x8000:
            val -= 0x10000
        return val

    @staticmethod
    def _decode_uint16(registers: list[int]) -> int:
        """Decode an unsigned 16-bit value from a single register."""
        return registers[0]

    @staticmethod
    def _decode_int32(registers: list[int]) -> int:
        """Decode a signed 32-bit value from two registers (big-endian)."""
        val = (registers[0] << 16) | registers[1]
        if val >= 0x80000000:
            val -= 0x100000000
        return val

    @staticmethod
    def _decode_uint32(registers: list[int]) -> int:
        """Decode an unsigned 32-bit value from two registers (big-endian)."""
        return (registers[0] << 16) | registers[1]

    async def _async_update_data(self) -> dict[str, float | int | None]:
        """Fetch all register data from the inverter."""
        try:
            client = await self._ensure_connected()
        except Exception as err:
            raise UpdateFailed(f"Connection failed: {err}") from err

        data: dict[str, float | int | None] = {}

        # Define all registers to read: (key, address, count, decoder, scale)
        registers_16: list[tuple[str, int, str, float]] = [
            # Inverter voltages
            ("inverter_voltage_l1", 1024, "uint16", 0.1),
            ("inverter_voltage_l2", 1025, "uint16", 0.1),
            ("inverter_voltage_l3", 1026, "uint16", 0.1),
            # Inverter mode
            ("inverter_mode", 1088, "int16", 1),
            # Inverter temperature
            ("inverter_temperature", 1077, "int16", 0.1),
            # Grid frequency
            ("grid_frequency", 1052, "int16", 0.01),
            # PV string voltages/currents
            ("pv1_voltage", 1053, "int16", 0.1),
            ("pv1_current", 1054, "int16", 0.1),
            ("pv2_voltage", 1057, "int16", 0.1),
            ("pv2_current", 1058, "int16", 0.1),
            # Battery
            ("battery_soc", 258, "int16", 0.1),
            ("battery_voltage", 256, "int16", 0.1),
            ("battery_power", 294, "int16", 1),
            ("battery_relay_status", 260, "int16", 1),
            ("battery_remaining_time", 295, "int16", 1),
            ("battery_ups_soc", 2128, "int16", 1),
            ("battery_min_cell_temp", 269, "uint16", 0.1),
            ("battery_max_cell_temp", 272, "uint16", 0.1),
            ("battery_max_charge_current", 273, "uint16", 0.1),
            ("battery_max_discharge_current", 274, "uint16", 0.1),
            # Settings
            ("max_feed_to_grid", 2048, "uint16", 1),
            # EMS versions
            ("ems_version_high", 1833, "uint16", 1),
            ("ems_version_middle", 1834, "uint16", 1),
            ("ems_version_low", 1835, "uint16", 1),
            # CT rates
            ("gridmeter_ct_rate", 1, "uint16", 1),
            ("pvmeter_ct_rate", 129, "uint16", 1),
            # Grid voltages
            ("grid_voltage_phase_a", 20, "uint16", 1),
            ("grid_voltage_phase_b", 21, "uint16", 1),
            ("grid_voltage_phase_c", 22, "uint16", 1),
        ]

        registers_32: list[tuple[str, int, str, float]] = [
            # Grid power
            ("total_power_grid", 33, "int32", 1),
            # PV meter
            ("total_power_pvmeter", 161, "int32", 1),
            # Inverter power
            ("total_power_inverter", 1036, "int32", 1),
            ("power_inverter_l1", 1030, "int32", 1),
            ("power_inverter_l2", 1032, "int32", 1),
            ("power_inverter_l3", 1034, "int32", 1),
            # Inverter backup
            ("power_inverter_backup_total", 1050, "uint32", 1),
            ("power_inverter_backup_l1", 1044, "uint32", 1),
            ("power_inverter_backup_l2", 1046, "uint32", 1),
            ("power_inverter_backup_l3", 1048, "uint32", 1),
            # PV strings
            ("power_string_1", 1055, "uint32", 1),
            ("power_string_2", 1059, "uint32", 1),
            ("power_string_3", 1063, "uint32", 1),
            ("power_string_4", 1067, "uint32", 1),
            # Energy statistics
            ("energy_feed_to_grid", 16, "uint32", 0.01),
            ("energy_consumption_from_grid", 18, "uint32", 0.01),
            ("energy_feed_to_grid_pvmeter", 144, "uint32", 0.01),
            ("energy_consumption_from_grid_pvmeter", 146, "uint32", 0.01),
            ("energy_charge_battery", 288, "uint32", 0.1),
            ("energy_discharge_battery", 290, "uint32", 0.1),
            ("energy_charge_battery_from_grid", 292, "uint32", 0.1),
            ("energy_from_pv", 1086, "uint32", 0.1),
            # Faults
            ("inverter_fault_1", 1082, "uint32", 1),
            ("inverter_fault_2", 1084, "uint32", 1),
            ("inverter_extended_fault_1", 1099, "uint32", 1),
            ("inverter_extended_fault_2", 1101, "uint32", 1),
            ("system_fault", 1793, "uint32", 1),
        ]

        # Read 16-bit registers (1 register each)
        for key, address, dtype, scale in registers_16:
            regs = await self._read_register(client, address, count=1)
            if regs is not None:
                if dtype == "int16":
                    raw = self._decode_int16(regs)
                else:
                    raw = self._decode_uint16(regs)
                data[key] = round(raw * scale, 2)
            else:
                data[key] = None

        # Read 32-bit registers (2 registers each)
        for key, address, dtype, scale in registers_32:
            regs = await self._read_register(client, address, count=2)
            if regs is not None:
                if dtype == "int32":
                    raw = self._decode_int32(regs)
                else:
                    raw = self._decode_uint32(regs)
                data[key] = round(raw * scale, 2)
            else:
                data[key] = None

        return data

    async def async_write_register(self, address: int, value: int) -> bool:
        """Write a value to a Modbus holding register."""
        try:
            client = await self._ensure_connected()
            result = await client.write_register(
                address=address,
                value=value,
                slave=self.slave_id,
            )
            if result.isError():
                _LOGGER.error("Error writing register %s: %s", address, result)
                return False
            return True
        except Exception as err:
            _LOGGER.error("Exception writing register %s: %s", address, err)
            return False

    async def async_shutdown(self) -> None:
        """Close the Modbus connection."""
        if self._client and self._client.connected:
            self._client.close()
            self._client = None
