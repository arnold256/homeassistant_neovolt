"""DataUpdateCoordinator for NeoVolt integration."""

from __future__ import annotations

import inspect
import logging
from datetime import timedelta

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Modbus bulk-read blocks
#
# Each block is read in a single Modbus request. Values are extracted by offset.
# Register map based on AlphaESS Modbus documentation v1.23, verified on Hi10.
#
# Block 1:  Grid Meter       start=1     count=34  (registers 1-34)
# Block 2:  PV Meter         start=129   count=34  (registers 129-162)
# Block 3:  Battery          start=256   count=47  (registers 256-302)
# Block 4:  Inverter         start=1024  count=65  (registers 1024-1088)
# Block 5:  Extended Faults  start=1099  count=4   (registers 1099-1102)
# Block 6:  EMS Version      start=1867  count=3   (registers 1867-1869)
# Block 8:  System Config    start=2048  count=1   (register 2048)
# Block 9:  Timing           start=2127  count=11  (registers 2127-2137)
# Block 10: Dispatch         start=2176  count=9   (registers 2176-2184)
# Block 11: System Op        start=2256  count=6   (registers 2256-2261)
# ──────────────────────────────────────────────────────────────────────────────

# Register definitions: (key, address, dtype, scale)
# dtype: u16=unsigned 16-bit, s16=signed 16-bit, u32=unsigned 32-bit, s32=signed 32-bit
REGISTER_DEFS: list[tuple[str, int, str, float]] = [
    # ── Grid Meter (block 1: start=1, count=34) ──
    ("gridmeter_ct_rate", 1, "u16", 1),                          # 0x0001
    ("energy_feed_to_grid", 16, "u32", 0.01),                    # 0x0010 kWh
    ("energy_consumption_from_grid", 18, "u32", 0.01),            # 0x0012 kWh
    ("grid_voltage_phase_a", 20, "u16", 1),                       # 0x0014 V
    ("grid_voltage_phase_b", 21, "u16", 1),                       # 0x0015 V
    ("grid_voltage_phase_c", 22, "u16", 1),                       # 0x0016 V
    ("grid_current_phase_a", 23, "s16", 0.1),                     # 0x0017 A
    ("grid_current_phase_b", 24, "s16", 0.1),                     # 0x0018 A
    ("grid_current_phase_c", 25, "s16", 0.1),                     # 0x0019 A
    ("grid_frequency_meter", 26, "u16", 0.01),                    # 0x001A Hz
    ("grid_power_phase_a", 27, "s32", 1),                         # 0x001B W
    ("grid_power_phase_b", 29, "s32", 1),                         # 0x001D W
    ("grid_power_phase_c", 31, "s32", 1),                         # 0x001F W
    ("total_power_grid", 33, "s32", 1),                           # 0x0021 W
    # ── PV Meter (block 2: start=129, count=34) ──
    ("pvmeter_ct_rate", 129, "u16", 1),                           # 0x0081
    ("energy_feed_to_grid_pvmeter", 144, "u32", 0.01),            # 0x0090 kWh
    ("energy_consumption_from_grid_pvmeter", 146, "u32", 0.01),   # 0x0092 kWh
    ("total_power_pvmeter", 161, "s32", 1),                       # 0x00A1 W
    # ── Battery (block 3: start=256, count=47) ──
    ("battery_voltage", 256, "u16", 0.1),                         # 0x0100 V
    ("battery_current", 257, "s16", 0.1),                         # 0x0101 A
    ("battery_soc", 258, "u16", 0.1),                             # 0x0102 %
    ("battery_status", 259, "u16", 1),                            # 0x0103 lookup
    ("battery_relay_status", 260, "u16", 1),                      # 0x0104 lookup
    ("battery_min_cell_temp", 269, "s16", 0.1),                   # 0x010D °C
    ("battery_max_cell_temp", 272, "s16", 0.1),                   # 0x0110 °C
    ("battery_max_charge_current", 273, "u16", 0.1),              # 0x0111 A
    ("battery_max_discharge_current", 274, "u16", 0.1),           # 0x0112 A
    ("battery_capacity", 281, "u16", 0.1),                        # 0x0119 kWh
    ("battery_soh", 283, "u16", 0.1),                             # 0x011B %
    ("energy_charge_battery", 288, "u32", 0.1),                   # 0x0120 kWh
    ("energy_discharge_battery", 290, "u32", 0.1),                # 0x0122 kWh
    ("energy_charge_battery_from_grid", 292, "u32", 0.1),         # 0x0124 kWh
    ("battery_power", 294, "s16", 1),                             # 0x0126 W
    ("battery_remaining_time", 295, "u16", 1),                    # 0x0127 minutes
    ("battery_max_charge_power", 300, "u16", 1),                  # 0x012C W
    ("battery_max_discharge_power", 301, "u16", 1),               # 0x012D W
    ("battery_mos_control", 302, "u16", 1),                       # 0x012E RW lookup
    # ── Inverter (block 4: start=1024, count=65) ──
    ("inverter_voltage_l1", 1024, "u16", 0.1),                    # 0x0400 V
    ("inverter_voltage_l2", 1025, "u16", 0.1),                    # 0x0401 V
    ("inverter_voltage_l3", 1026, "u16", 0.1),                    # 0x0402 V
    ("inverter_current_l1", 1027, "s16", 0.1),                    # 0x0403 A
    ("inverter_current_l2", 1028, "s16", 0.1),                    # 0x0404 A
    ("inverter_current_l3", 1029, "s16", 0.1),                    # 0x0405 A
    ("power_inverter_l1", 1030, "s32", 1),                        # 0x0406 W
    ("power_inverter_l2", 1032, "s32", 1),                        # 0x0408 W
    ("power_inverter_l3", 1034, "s32", 1),                        # 0x040A W
    ("total_power_inverter", 1036, "s32", 1),                     # 0x040C W
    ("power_inverter_backup_l1", 1044, "u32", 1),                 # 0x0414 W
    ("power_inverter_backup_l2", 1046, "u32", 1),                 # 0x0416 W
    ("power_inverter_backup_l3", 1048, "u32", 1),                 # 0x0418 W
    ("power_inverter_backup_total", 1050, "u32", 1),              # 0x041A W
    ("grid_frequency", 1052, "u16", 0.01),                        # 0x041C Hz
    ("pv1_voltage", 1053, "u16", 0.1),                            # 0x041D V
    ("pv1_current", 1054, "u16", 0.1),                            # 0x041E A
    ("power_string_1", 1055, "u32", 1),                           # 0x041F W
    ("pv2_voltage", 1057, "u16", 0.1),                            # 0x0421 V
    ("pv2_current", 1058, "u16", 0.1),                            # 0x0422 A
    ("power_string_2", 1059, "u32", 1),                           # 0x0423 W
    ("pv3_voltage", 1061, "u16", 0.1),                            # 0x0425 V
    ("pv3_current", 1062, "u16", 0.1),                            # 0x0426 A
    ("power_string_3", 1063, "u32", 1),                           # 0x0427 W
    ("pv4_voltage", 1065, "u16", 0.1),                            # 0x0429 V
    ("pv4_current", 1066, "u16", 0.1),                            # 0x042A A
    ("power_string_4", 1067, "u32", 1),                           # 0x042B W
    ("inverter_temperature", 1077, "u16", 0.1),                   # 0x0435 °C
    ("inverter_warning_1", 1078, "u32", 1),                       # 0x0436
    ("inverter_warning_2", 1080, "u32", 1),                       # 0x0438
    ("inverter_fault_1", 1082, "u32", 1),                         # 0x043A
    ("inverter_fault_2", 1084, "u32", 1),                         # 0x043C
    ("energy_from_pv", 1086, "u32", 0.1),                         # 0x043E kWh
    ("inverter_mode", 1088, "u16", 1),                            # 0x0440 lookup
    # ── Extended Faults (block 5: start=1099, count=4) ──
    ("inverter_extended_fault_1", 1099, "u32", 1),                # 0x044B
    ("inverter_extended_fault_2", 1101, "u32", 1),                # 0x044D
    # ── EMS Version (block 6: start=1867, count=3) ──
    ("ems_version_high", 1867, "u16", 1),                         # 0x074B
    ("ems_version_middle", 1868, "u16", 1),                       # 0x074C
    ("ems_version_low", 1869, "u16", 1),                          # 0x074D
    # ── System Config (block 7: start=2048, count=1) ──
    ("max_feed_to_grid", 2048, "u16", 1),                         # 0x0800 %
    # ── Timing (block 8: start=2127, count=11) ──
    ("time_period_control_flag", 2127, "u16", 1),                 # 0x084F lookup
    ("battery_ups_soc", 2128, "u16", 1),                          # 0x0850 %
    ("discharge_start_time_1", 2129, "u16", 1),                   # 0x0851 hr
    ("discharge_stop_time_1", 2130, "u16", 1),                    # 0x0852 hr
    ("discharge_start_time_2", 2131, "u16", 1),                   # 0x0853 hr
    ("discharge_stop_time_2", 2132, "u16", 1),                    # 0x0854 hr
    ("charge_cut_soc", 2133, "u16", 0.1),                         # 0x0855 %
    ("charge_start_time_1", 2134, "u16", 1),                      # 0x0856 hr
    ("charge_stop_time_1", 2135, "u16", 1),                       # 0x0857 hr
    ("charge_start_time_2", 2136, "u16", 1),                      # 0x0858 hr
    ("charge_stop_time_2", 2137, "u16", 1),                       # 0x0859 hr
    # ── Dispatch (block 9: start=2176, count=9) ──
    ("dispatch_start", 2176, "u16", 1),                           # 0x0880 lookup
    ("dispatch_active_power", 2177, "s32", 1),                    # 0x0881 W
    ("dispatch_reactive_power", 2179, "s32", 1),                  # 0x0883 var
    ("dispatch_mode", 2181, "u16", 1),                            # 0x0885 lookup
    ("dispatch_soc", 2182, "u16", 0.4),                           # 0x0886 %
    ("dispatch_time", 2183, "u32", 1),                            # 0x0887 s
    # ── System Operational (block 10: start=2256, count=6) ──
    ("pv_inverter_energy", 2256, "u32", 0.1),                     # 0x08D0 kWh
    ("system_total_pv_energy", 2258, "u32", 0.1),                 # 0x08D2 kWh
    ("system_fault", 2260, "u32", 1),                             # 0x08D4
]

# Bulk-read blocks: (start_address, count)
READ_BLOCKS: list[tuple[int, int]] = [
    (1, 34),       # Block 1:  Grid Meter
    (129, 34),     # Block 2:  PV Meter
    (256, 47),     # Block 3:  Battery (extended to include register 302)
    (1024, 65),    # Block 4:  Inverter
    (1099, 4),     # Block 5:  Extended Faults
    (1867, 3),     # Block 6:  EMS Version
    (2048, 1),     # Block 8:  System Config
    (2127, 11),    # Block 9:  Timing
    (2176, 9),     # Block 10: Dispatch
    (2256, 6),     # Block 11: System Operational
]


class NeoVoltCoordinator(DataUpdateCoordinator[dict[str, float | int | str | None]]):
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

        # pymodbus 3.6-3.8 uses slave=, 3.12+ uses device_id=
        sig = inspect.signature(AsyncModbusTcpClient.read_holding_registers)
        if "device_id" in sig.parameters:
            self._slave_kwarg = {"device_id": slave_id}
        else:
            self._slave_kwarg = {"slave": slave_id}

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

    async def _read_block(
        self,
        client: AsyncModbusTcpClient,
        start: int,
        count: int,
    ) -> list[int] | None:
        """Read a contiguous block of holding registers."""
        try:
            result = await client.read_holding_registers(
                start, count=count, **self._slave_kwarg,
            )
            if result.isError():
                _LOGGER.debug(
                    "Error reading block start=%s count=%s: %s", start, count, result
                )
                return None
            return list(result.registers)
        except (ModbusException, AttributeError) as err:
            _LOGGER.debug(
                "Exception reading block start=%s count=%s: %s", start, count, err
            )
            return None

    @staticmethod
    def _extract_u16(registers: list[int], offset: int) -> int:
        return registers[offset]

    @staticmethod
    def _extract_s16(registers: list[int], offset: int) -> int:
        val = registers[offset]
        return val - 0x10000 if val >= 0x8000 else val

    @staticmethod
    def _extract_u32(registers: list[int], offset: int) -> int:
        return (registers[offset] << 16) | registers[offset + 1]

    @staticmethod
    def _extract_s32(registers: list[int], offset: int) -> int:
        val = (registers[offset] << 16) | registers[offset + 1]
        return val - 0x100000000 if val >= 0x80000000 else val

    def _extract(self, registers: list[int], offset: int, dtype: str) -> int:
        if dtype == "u16":
            return self._extract_u16(registers, offset)
        if dtype == "s16":
            return self._extract_s16(registers, offset)
        if dtype == "u32":
            return self._extract_u32(registers, offset)
        return self._extract_s32(registers, offset)

    async def _async_update_data(self) -> dict[str, float | int | str | None]:
        """Fetch all register data from the inverter."""
        try:
            client = await self._ensure_connected()
        except Exception as err:
            raise UpdateFailed(f"Connection failed: {err}") from err

        blocks: dict[int, list[int]] = {}
        for start, count in READ_BLOCKS:
            regs = await self._read_block(client, start, count)
            if regs is not None:
                blocks[start] = regs

        data: dict[str, float | int | str | None] = {}

        for key, address, dtype, scale in REGISTER_DEFS:
            block_regs = None
            block_start = 0
            for start, count in READ_BLOCKS:
                if start <= address < start + count:
                    block_regs = blocks.get(start)
                    block_start = start
                    break

            if block_regs is None:
                data[key] = None
                continue

            offset = address - block_start
            raw = self._extract(block_regs, offset, dtype)
            data[key] = round(raw * scale, 2)

        return data

    async def async_write_register(self, address: int, value: int) -> bool:
        """Write a single value to a Modbus holding register."""
        try:
            client = await self._ensure_connected()
            result = await client.write_register(
                address, value, **self._slave_kwarg,
            )
            if result.isError():
                _LOGGER.error("Error writing register %s: %s", address, result)
                return False
            return True
        except Exception as err:
            _LOGGER.error("Exception writing register %s: %s", address, err)
            return False

    async def async_write_registers(self, address: int, values: list[int]) -> bool:
        """Write multiple values to consecutive Modbus holding registers."""
        try:
            client = await self._ensure_connected()
            result = await client.write_registers(
                address, values, **self._slave_kwarg,
            )
            if result.isError():
                _LOGGER.error("Error writing registers %s: %s", address, result)
                return False
            return True
        except Exception as err:
            _LOGGER.error("Exception writing registers %s: %s", address, err)
            return False

    async def async_readback_register(
        self, address: int, count: int = 1
    ) -> list[int] | None:
        """Read back register(s) immediately after a write to confirm the change."""
        try:
            client = await self._ensure_connected()
        except Exception:
            return None
        return await self._read_block(client, address, count)

    async def async_write_and_readback(
        self, address: int, value: int, key: str, scale: float, dtype: str
    ) -> bool:
        """Write a 16-bit register, read it back, and update coordinator data."""
        success = await self.async_write_register(address, value)
        if not success:
            return False

        regs = await self.async_readback_register(address, count=1)
        if regs is not None:
            raw = self._extract(regs, 0, dtype)
            self.data[key] = round(raw * scale, 2)
            _LOGGER.debug(
                "Readback register %s: wrote %s, read back %s",
                address, value, self.data[key],
            )
        return True

    async def async_write_and_readback_32(
        self, address: int, values: list[int], key: str, scale: float, dtype: str
    ) -> bool:
        """Write a 32-bit register pair, read back, and update coordinator data."""
        success = await self.async_write_registers(address, values)
        if not success:
            return False

        regs = await self.async_readback_register(address, count=2)
        if regs is not None:
            raw = self._extract(regs, 0, dtype)
            self.data[key] = round(raw * scale, 2)
            _LOGGER.debug(
                "Readback registers %s: wrote %s, read back %s",
                address, values, self.data[key],
            )
        return True

    async def async_shutdown(self) -> None:
        """Close the Modbus connection."""
        if self._client and self._client.connected:
            self._client.close()
            self._client = None
