# NeoVolt - AlphaESS Modbus Integration for Home Assistant

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=arnold256&repository=homeassistant_neovolt&category=integration)

## Introduction

NeoVolt integrates AlphaESS solar battery storage systems into Home Assistant via **Modbus TCP**. It provides real-time monitoring of solar production, battery status, grid power, and energy statistics -- all accessible on the Home Assistant **Energy Dashboard** out of the box.

## Compatibility

- AlphaESS Smile Hi10 with 7.8 kWh battery (tested)
- Other AlphaESS systems with Modbus TCP interface (should work -- register layout may vary)

## Features

- **UI-based setup** -- add devices by entering just the IP address (no YAML editing required)
- **Multiple devices** -- add as many inverters as you have, each with its own IP
- **Energy Dashboard ready** -- all energy sensors have the correct `device_class` and `state_class` so they appear directly in the Energy Dashboard
- **Battery monitoring** -- SOC, voltage, temperature, charge/discharge power and current
- **PV string tracking** -- per-string power, voltage, and current
- **Grid monitoring** -- power, voltage per phase, frequency
- **Writable controls** -- sliders for "Max Feed to Grid Rate" and "Target SOC"
- **Fault monitoring** -- inverter and system fault codes

## Installation via HACS

1. Open Home Assistant
2. Go to **HACS** > **Integrations**
3. Click the **three dots** menu (top right) > **Custom repositories**
4. Enter the repository URL: `https://github.com/arnold256/homeassistant_neovolt`
5. Select category: **Integration**
6. Click **Add**
7. Search for **NeoVolt** in HACS and click **Download**
8. **Restart Home Assistant**

Or click the button at the top of this page to add the repository directly.

## Setup

1. After restart, go to **Settings** > **Devices & Services**
2. Click **Add Integration** and search for **NeoVolt**
3. Enter the **IP address** of your AlphaESS inverter
4. Port defaults to `502` and Slave ID to `85` (change only if your system differs)
5. Click **Submit** -- the integration will verify the connection

To add another device, simply repeat the steps above with a different IP address.

## Energy Dashboard

The following sensors are automatically available for the Energy Dashboard:

| Dashboard Section | Sensor |
|---|---|
| **Solar Production** | Total Energy from PV |
| **Grid Consumption** | Total Energy Consumption from Grid |
| **Return to Grid** | Total Energy Feed to Grid |
| **Battery Charge** | Total Energy Charge Battery |
| **Battery Discharge** | Total Energy Discharge Battery |

All energy sensors use `kWh` with `device_class: energy` and `state_class: total_increasing`.

## Sensors

The integration creates sensors for:

- **Grid**: total power, per-phase voltage
- **Inverter**: total and per-phase power, voltage, temperature, frequency, mode, faults
- **PV Strings**: power, voltage, and current for strings 1-4
- **Battery**: SOC, voltage, power, temperature (min/max cell), charge/discharge current, relay status, remaining time
- **Energy totals**: feed to grid, consumption from grid, battery charge/discharge, PV generation
- **Controls** (Number entities): Target SOC, Max Feed to Grid Rate

## Prerequisites

- Home Assistant 2024.1 or later
- AlphaESS system with Modbus TCP enabled
- Network connectivity between Home Assistant and the inverter

## Links

- [AlphaESS Modbus TCP Documentation (German)](https://www.alpha-ess.de/images/downloads/handbuecher/AlphaESS-Handbuch_SMILE_ModBus_RTU_TCP_V21.pdf)
- [AlphaESS Register Parameter List (German)](https://www.alpha-ess.de/images/downloads/handbuecher/AlphaESS_Register_Parameter_List.pdf)

## Warnings

- **Everything provided here is without warranty.**
- **Please be careful when writing registers -- incorrect values can affect your system.**
- **Only the Smile Hi10 system has been tested.**
- **Use at your own risk.**
