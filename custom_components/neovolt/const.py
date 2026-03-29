"""Constants for the NeoVolt integration."""

DOMAIN = "neovolt"

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 85
DEFAULT_SCAN_INTERVAL = 10

CONF_SLAVE_ID = "slave_id"
CONF_SCAN_INTERVAL = "scan_interval"

# ── Status lookup maps ──

BATTERY_RELAY_STATUS_MAP: dict[int, str] = {
    0: "Disconnected",
    1: "Discharge Only",
    2: "Charge Only",
    3: "Normal",
}

INVERTER_MODE_MAP: dict[int, str] = {
    0: "Wait",
    1: "Online",
    2: "UPS",
    3: "Bypass",
    4: "Fault",
    5: "DC",
    6: "Check",
    7: "Self Test",
    8: "Update Master",
    9: "Update Slave",
    10: "Update ARM",
}

# Battery MOS Control — excludes 0 (Disconnected) to prevent accidental battery disconnect
BATTERY_MOS_CONTROL_OPTIONS: dict[int, str] = {
    1: "Discharge Only",
    2: "Charge Only",
    3: "Normal",
}

DISPATCH_START_MAP: dict[int, str] = {
    0: "Off",
    1: "On",
}

DISPATCH_MODE_MAP: dict[int, str] = {
    0: "Normal",
    1: "Charge",
    2: "Discharge",
}

TIME_PERIOD_CONTROL_MAP: dict[int, str] = {
    0: "Disable",
    1: "Enable Charge Time Period Control",
    2: "Enable Discharge Time Period Control",
    3: "Enable Time Period Control",
}

# SOC conversion for dispatch registers (0-255 range)
SOC_CONVERSION_FACTOR = 2.55

# Dispatch reset values (11 registers written to 0x0880)
MODBUS_OFFSET = 32000
DISPATCH_RESET_VALUES = [0, 0, MODBUS_OFFSET, 0, MODBUS_OFFSET, 0, 0, 0, 90, 255, 0]
