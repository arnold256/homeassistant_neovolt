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
# Aligned with pvandenh/NeovoltBattery_ModbusPlugin register map.
REGISTER_DEFS: list[tuple[str, int, str, float]] = [
    # ── Grid Meter (block: 0x0010, 39 registers) ──
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
    ("grid_power_factor", 54, "s16", 0.01),                       # 0x0036
    # ── PV Meter (block: 0x0090, 20 registers) ──
    ("energy_feed_to_grid_pvmeter", 144, "u32", 0.01),            # 0x0090 kWh
    ("energy_consumption_from_grid_pvmeter", 146, "u32", 0.01),   # 0x0092 kWh
    ("pv_voltage_a", 148, "u16", 1),                              # 0x0094 V
    ("total_power_pvmeter", 161, "s32", 1),                       # 0x00A1 W
    # ── Battery (block: 0x0100, 40 registers) ──
    ("battery_voltage", 256, "u16", 0.1),                         # 0x0100 V
    ("battery_current", 257, "s16", 0.1),                         # 0x0101 A
    ("battery_soc", 258, "u16", 0.1),                             # 0x0102 %
    ("battery_status", 259, "u16", 1),                            # 0x0103 lookup
    ("battery_relay_status", 260, "u16", 1),                      # 0x0104 lookup
    ("battery_min_cell_voltage", 263, "u16", 0.001),              # 0x0107 V
    ("battery_max_cell_voltage", 266, "u16", 0.001),              # 0x010A V
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
    # ── Inverter (block: 0x0400, 65 registers) ──
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
    # ── Extended Faults (block: 0x044B, 4 registers) ──
    ("inverter_extended_fault_1", 1099, "u32", 1),                # 0x044B
    ("inverter_extended_fault_2", 1101, "u32", 1),                # 0x044D
    # ── EMS Version (block: 0x074B, 3 registers) ──
    ("ems_version_high", 1867, "u16", 1),                         # 0x074B
    ("ems_version_middle", 1868, "u16", 1),                       # 0x074C
    ("ems_version_low", 1869, "u16", 1),                          # 0x074D
    # ── Settings (block: 0x0800, 86 registers) ──
    ("max_feed_to_grid", 2048, "u16", 1),                         # 0x0800 %
    ("pv_capacity", 2049, "u32", 1),                              # 0x0801 W (writable)
    ("time_period_control_flag", 2127, "u16", 1),                 # 0x084F lookup
    ("discharging_cutoff_soc", 2128, "u16", 1),                   # 0x0850 %
    ("discharge_start_time_1", 2129, "u16", 1),                   # 0x0851 hr
    ("discharge_stop_time_1", 2130, "u16", 1),                    # 0x0852 hr
    ("discharge_start_time_2", 2131, "u16", 1),                   # 0x0853 hr
    ("discharge_stop_time_2", 2132, "u16", 1),                    # 0x0854 hr
    ("charging_cutoff_soc", 2133, "u16", 1),                      # 0x0855 % (raw, no scale)
    ("charge_start_time_1", 2134, "u16", 1),                      # 0x0856 hr
    ("charge_stop_time_1", 2135, "u16", 1),                       # 0x0857 hr
    ("charge_start_time_2", 2136, "u16", 1),                      # 0x0858 hr
    ("charge_stop_time_2", 2137, "u16", 1),                       # 0x0859 hr
    ("discharge_start_time_1_min", 2138, "u16", 1),               # 0x085A min
    ("discharge_stop_time_1_min", 2139, "u16", 1),                # 0x085B min
    ("discharge_start_time_2_min", 2140, "u16", 1),               # 0x085C min
    ("discharge_stop_time_2_min", 2141, "u16", 1),                # 0x085D min
    ("charge_start_time_1_min", 2142, "u16", 1),                  # 0x085E min
    ("charge_stop_time_1_min", 2143, "u16", 1),                   # 0x085F min
    ("charge_start_time_2_min", 2144, "u16", 1),                  # 0x0860 min
    ("charge_stop_time_2_min", 2145, "u16", 1),                   # 0x0861 min
    # ── Dispatch (block: 0x0880, 11 registers) ──
    # Power uses OFFSET 32000. SOC uses factor 2.55 (0-255 range).
    # Must be written as single 11-register block, not individual writes.
    ("dispatch_start", 2176, "u16", 1),                           # 0x0880
    ("dispatch_active_power_raw", 2177, "u32", 1),                # 0x0881 raw (offset 32000)
    ("dispatch_reactive_power_raw", 2179, "u32", 1),              # 0x0883 raw (offset 32000)
    ("dispatch_mode", 2181, "u16", 1),                            # 0x0885
    ("dispatch_soc_raw", 2182, "u16", 1),                         # 0x0886 raw (0-255, factor 2.55)
    ("dispatch_time", 2183, "u32", 1),                            # 0x0887 seconds
    ("dispatch_energy_routing", 2185, "u16", 1),                  # 0x0889
    ("dispatch_pv_switch", 2186, "u16", 1),                       # 0x088A
    # ── System Operational (block: 0x08D0, 6 registers) ──
    ("pv_inverter_energy", 2256, "u32", 0.01),                    # 0x08D0 kWh (pvandenh: 0.01)
    ("system_total_pv_energy", 2258, "u32", 0.1),                 # 0x08D2 kWh
    ("system_fault", 2260, "u32", 1),                             # 0x08D4
    # ── Calibration (block: 0x11D3, 3 registers) ──
    ("grid_power_offset", 4565, "s16", 1),                        # 0x11D5 W (-500 to +500)
]

# Bulk-read blocks: (start_address, count)
READ_BLOCKS: list[tuple[int, int]] = [
    (16, 39),      # Block 1:  Grid Meter (0x0010, covers to 0x0036)
    (144, 20),     # Block 2:  PV Meter (0x0090)
    (256, 47),     # Block 3:  Battery (0x0100, extended to 302)
    (1024, 65),    # Block 4:  Inverter (0x0400)
    (1099, 4),     # Block 5:  Extended Faults (0x044B)
    (1867, 3),     # Block 6:  EMS Version (0x074B)
    (2048, 98),    # Block 7:  Settings (0x0800, covers 2048-2145)
    (2176, 11),    # Block 8:  Dispatch (0x0880)
    (2256, 6),     # Block 9:  System Operational (0x08D0)
    (4563, 3),     # Block 10: Calibration (0x11D3)
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

        # Post-process dispatch values
        # Power: offset-32000 encoding → signed watts
        raw_active = data.get("dispatch_active_power_raw")
        data["dispatch_active_power"] = (
            int(raw_active) - 32000 if raw_active is not None else None
        )
        raw_reactive = data.get("dispatch_reactive_power_raw")
        data["dispatch_reactive_power"] = (
            int(raw_reactive) - 32000 if raw_reactive is not None else None
        )
        # SOC: factor 2.55 (0-255 register → 0-100%)
        raw_soc = data.get("dispatch_soc_raw")
        data["dispatch_soc"] = (
            round(int(raw_soc) / 2.55, 1) if raw_soc is not None else None
        )

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

    async def async_dispatch_start(
        self,
        active_power_w: int,
        duration_s: int,
        mode: int = 2,
        soc_pct: float = 0,
        reactive_power_var: int = 0,
    ) -> bool:
        """Start dispatch by writing all 11 registers as a single block to 0x0880.

        The NeoVolt requires all dispatch parameters written as a single
        multi-register write to address 0x0880 (11 registers).

        Args:
            active_power_w: Watts, negative=charge, positive=discharge.
            duration_s: Duration in seconds.
            mode: Dispatch mode (0=Power only, 2=Power+SOC, 19=No battery charge).
            soc_pct: Target SOC percentage (0-100).
            reactive_power_var: Reactive power in var (usually 0).
        """
        # Convert to register encoding
        active_raw = 32000 + active_power_w
        reactive_raw = 32000 + reactive_power_var
        soc_raw = max(0, min(255, round(soc_pct * 2.55)))

        _LOGGER.info(
            "Dispatch start: %dW, %ds, mode=%d, soc=%.0f%% (raw=%d), reactive=%dvar",
            active_power_w, duration_s, mode, soc_pct, soc_raw, reactive_power_var,
        )

        # Build 11-register block: [Para1, Para2_hi, Para2_lo, Para3_hi, Para3_lo,
        #                            Para4, Para5, Para6_hi, Para6_lo, Para7, Para8]
        values = [
            1,                              # Para1: dispatch_start = On
            (active_raw >> 16) & 0xFFFF,    # Para2 high: active power
            active_raw & 0xFFFF,            # Para2 low
            (reactive_raw >> 16) & 0xFFFF,  # Para3 high: reactive power
            reactive_raw & 0xFFFF,          # Para3 low
            mode,                           # Para4: dispatch mode
            soc_raw,                        # Para5: SOC target (0-255)
            (duration_s >> 16) & 0xFFFF,    # Para6 high: duration
            duration_s & 0xFFFF,            # Para6 low
            0,                              # Para7: energy routing
            0,                              # Para8: PV switch (0=Auto)
        ]

        ok = await self.async_write_registers(2176, values)
        if ok:
            await self.async_request_refresh()
        return ok

    async def async_dispatch_stop(self) -> bool:
        """Stop dispatch by writing reset values to 0x0880 (11 registers)."""
        _LOGGER.info("Dispatch stop")
        reset_values = [0, 0, 32000, 0, 32000, 0, 0, 0, 90, 255, 0]
        ok = await self.async_write_registers(2176, reset_values)
        if ok:
            await self.async_request_refresh()
        return ok

    async def async_shutdown(self) -> None:
        """Close the Modbus connection."""
        if self._client and self._client.connected:
            self._client.close()
            self._client = None
