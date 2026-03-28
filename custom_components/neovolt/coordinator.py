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

# ──────────────────────────────────────────────────────────────────────────────
# Modbus bulk-read blocks
#
# Each block is read in a single Modbus request. Values are extracted by offset.
# Register map based on AlphaESS Modbus documentation v1.23.
#
# Block 1: Grid Meter     start=1    count=34   (registers 1-34)
# Block 2: PV Meter       start=129  count=34   (registers 129-162)
# Block 3: Battery         start=256  count=40   (registers 256-295)
# Block 4: Inverter        start=1024 count=65   (registers 1024-1088)
# Block 5: Extended Faults start=1099 count=4    (registers 1099-1102)
# Block 6: EMS Version     start=1867 count=3    (registers 1867-1869)
# Block 7: System Config   start=2048 count=1    (register 2048)
# Block 8: UPS SOC         start=2128 count=1    (register 2128)
# Block 9: System Fault    start=2260 count=2    (registers 2260-2261)
# ──────────────────────────────────────────────────────────────────────────────

# Register definitions: (key, address, dtype, scale)
# dtype: u16=unsigned 16-bit, s16=signed 16-bit, u32=unsigned 32-bit, s32=signed 32-bit
REGISTER_DEFS: list[tuple[str, int, str, float]] = [
    # ── Grid Meter (block 1: start=1, count=34) ──
    ("gridmeter_ct_rate", 1, "u16", 1),           # 0x0001
    ("energy_feed_to_grid", 16, "u32", 0.01),      # 0x0010 kWh
    ("energy_consumption_from_grid", 18, "u32", 0.01),  # 0x0012 kWh
    ("grid_voltage_phase_a", 20, "u16", 1),         # 0x0014 V
    ("grid_voltage_phase_b", 21, "u16", 1),         # 0x0015 V
    ("grid_voltage_phase_c", 22, "u16", 1),         # 0x0016 V
    ("total_power_grid", 33, "s32", 1),             # 0x0021 W
    # ── PV Meter (block 2: start=129, count=34) ──
    ("pvmeter_ct_rate", 129, "u16", 1),             # 0x0081
    ("energy_feed_to_grid_pvmeter", 144, "u32", 0.01),  # 0x0090 kWh
    ("energy_consumption_from_grid_pvmeter", 146, "u32", 0.01),  # 0x0092 kWh
    ("total_power_pvmeter", 161, "s32", 1),         # 0x00A1 W
    # ── Battery (block 3: start=256, count=40) ──
    ("battery_voltage", 256, "u16", 0.1),           # 0x0100 V
    ("battery_current", 257, "s16", 0.1),           # 0x0101 A
    ("battery_soc", 258, "u16", 0.1),               # 0x0102 %
    ("battery_relay_status", 260, "u16", 1),        # 0x0104
    ("battery_min_cell_temp", 269, "s16", 0.1),     # 0x010D °C
    ("battery_max_cell_temp", 272, "s16", 0.1),     # 0x0110 °C
    ("battery_max_charge_current", 273, "u16", 0.1),  # 0x0111 A
    ("battery_max_discharge_current", 274, "u16", 0.1),  # 0x0112 A
    ("energy_charge_battery", 288, "u32", 0.1),     # 0x0120 kWh
    ("energy_discharge_battery", 290, "u32", 0.1),  # 0x0122 kWh
    ("energy_charge_battery_from_grid", 292, "u32", 0.1),  # 0x0124 kWh
    ("battery_power", 294, "s16", 1),               # 0x0126 W
    ("battery_remaining_time", 295, "u16", 1),      # 0x0127 minutes
    # ── Inverter (block 4: start=1024, count=65) ──
    ("inverter_voltage_l1", 1024, "u16", 0.1),      # 0x0400 V
    ("inverter_voltage_l2", 1025, "u16", 0.1),      # 0x0401 V
    ("inverter_voltage_l3", 1026, "u16", 0.1),      # 0x0402 V
    ("power_inverter_l1", 1030, "s32", 1),           # 0x0406 W
    ("power_inverter_l2", 1032, "s32", 1),           # 0x0408 W
    ("power_inverter_l3", 1034, "s32", 1),           # 0x040A W
    ("total_power_inverter", 1036, "s32", 1),        # 0x040C W
    ("power_inverter_backup_l1", 1044, "u32", 1),    # 0x0414 W
    ("power_inverter_backup_l2", 1046, "u32", 1),    # 0x0416 W
    ("power_inverter_backup_l3", 1048, "u32", 1),    # 0x0418 W
    ("power_inverter_backup_total", 1050, "u32", 1),  # 0x041A W
    ("grid_frequency", 1052, "u16", 0.1),            # 0x041C Hz
    ("pv1_voltage", 1053, "u16", 0.1),               # 0x041D V
    ("pv1_current", 1054, "u16", 0.1),               # 0x041E A
    ("power_string_1", 1055, "u32", 1),              # 0x041F W
    ("pv2_voltage", 1057, "u16", 0.1),               # 0x0421 V
    ("pv2_current", 1058, "u16", 0.1),               # 0x0422 A
    ("power_string_2", 1059, "u32", 1),              # 0x0423 W
    ("power_string_3", 1063, "u32", 1),              # 0x0427 W
    ("power_string_4", 1067, "u32", 1),              # 0x042B W
    ("inverter_temperature", 1077, "u16", 0.1),      # 0x0435 °C
    ("inverter_fault_1", 1082, "u32", 1),            # 0x043A
    ("inverter_fault_2", 1084, "u32", 1),            # 0x043C
    ("energy_from_pv", 1086, "u32", 0.1),            # 0x043E kWh
    ("inverter_mode", 1088, "u16", 1),               # 0x0440
    # ── Extended Faults (block 5: start=1099, count=4) ──
    ("inverter_extended_fault_1", 1099, "u32", 1),   # 0x044B
    ("inverter_extended_fault_2", 1101, "u32", 1),   # 0x044D
    # ── EMS Version (block 6: start=1867, count=3) ──
    ("ems_version_high", 1867, "u16", 1),            # 0x074B
    ("ems_version_middle", 1868, "u16", 1),          # 0x074C
    ("ems_version_low", 1869, "u16", 1),             # 0x074D
    # ── System Config (block 7: start=2048, count=1) ──
    ("max_feed_to_grid", 2048, "u16", 1),            # 0x0800 %
    # ── UPS SOC (block 8: start=2128, count=1) ──
    ("battery_ups_soc", 2128, "u16", 0.1),           # 0x0850 %
    # ── System Fault (block 9: start=2260, count=2) ──
    ("system_fault", 2260, "u32", 1),                # 0x08D4
]

# Bulk-read blocks: (start_address, count)
READ_BLOCKS: list[tuple[int, int]] = [
    (1, 34),       # Block 1: Grid Meter
    (129, 34),     # Block 2: PV Meter
    (256, 40),     # Block 3: Battery
    (1024, 65),    # Block 4: Inverter
    (1099, 4),     # Block 5: Extended Faults
    (1867, 3),     # Block 6: EMS Version
    (2048, 1),     # Block 7: System Config
    (2128, 1),     # Block 8: UPS SOC
    (2260, 2),     # Block 9: System Fault
]


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

    async def _read_block(
        self,
        client: AsyncModbusTcpClient,
        start: int,
        count: int,
    ) -> list[int] | None:
        """Read a contiguous block of holding registers."""
        try:
            result = await client.read_holding_registers(
                address=start,
                count=count,
                slave=self.slave_id,
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
        """Extract unsigned 16-bit value at offset."""
        return registers[offset]

    @staticmethod
    def _extract_s16(registers: list[int], offset: int) -> int:
        """Extract signed 16-bit value at offset."""
        val = registers[offset]
        return val - 0x10000 if val >= 0x8000 else val

    @staticmethod
    def _extract_u32(registers: list[int], offset: int) -> int:
        """Extract unsigned 32-bit value at offset (big-endian, 2 registers)."""
        return (registers[offset] << 16) | registers[offset + 1]

    @staticmethod
    def _extract_s32(registers: list[int], offset: int) -> int:
        """Extract signed 32-bit value at offset (big-endian, 2 registers)."""
        val = (registers[offset] << 16) | registers[offset + 1]
        return val - 0x100000000 if val >= 0x80000000 else val

    def _extract(
        self, registers: list[int], offset: int, dtype: str
    ) -> int:
        """Extract a value from a register block."""
        if dtype == "u16":
            return self._extract_u16(registers, offset)
        if dtype == "s16":
            return self._extract_s16(registers, offset)
        if dtype == "u32":
            return self._extract_u32(registers, offset)
        return self._extract_s32(registers, offset)

    async def _async_update_data(self) -> dict[str, float | int | None]:
        """Fetch all register data from the inverter."""
        try:
            client = await self._ensure_connected()
        except Exception as err:
            raise UpdateFailed(f"Connection failed: {err}") from err

        # Read all blocks
        blocks: dict[int, list[int]] = {}
        for start, count in READ_BLOCKS:
            regs = await self._read_block(client, start, count)
            if regs is not None:
                blocks[start] = regs

        # Extract individual values
        data: dict[str, float | int | None] = {}
        for key, address, dtype, scale in REGISTER_DEFS:
            # Find which block contains this register
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
