<p align="center">
  <img src="images/logo.png" alt="ABB Terra AC (ChargerSync) for Home Assistant" height="120">
</p>

<h1 align="center">ABB Terra AC — ChargerSync for Home Assistant</h1>

<p align="center">
  Control and monitor your <b>ABB Terra AC</b> EV wallbox from Home Assistant — entirely over the
  ChargeDot/ChargerSync <b>cloud</b>. No Modbus, no OCPP, no local network access to the charger required.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <img src="https://img.shields.io/badge/version-0.1.0-green.svg" alt="version">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="license">
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.6%2B-41BDF5.svg" alt="HA">
</p>

---

> [!WARNING]
> **Unofficial & unaffiliated.** This is a community integration built by reverse-engineering the
> ChargerSync mobile app's cloud protocol. It is **not** affiliated with, endorsed by, or supported by
> ABB or ChargeDot. The cloud API is undocumented and may change or break at any time. Use at your own risk.

## Why this exists

The ABB Terra AC is normally controlled via the ChargerSync phone app (cloud) or, locally, via Modbus/OCPP
(which need same-network access and installer/TerraConfig credentials). If your charger sits on a **different
network** and you can't get TerraConfig, neither local option works. This integration talks to the **same
cloud** the app uses, so it works from anywhere the charger has internet.

## Features

| Entity | Type | Description |
|--------|------|-------------|
| `switch.*_charging` | Switch | **Start / stop** a charging session |
| `binary_sensor.*_online` | Binary sensor | Charger online (connectivity) |
| `sensor.*_last_session_energy` | Sensor | Energy delivered in the last session (kWh) |
| `sensor.*_last_session_cost` | Sensor | Cost of the last session |
| `sensor.*_last_session_duration` | Sensor | Duration of the last session |
| `sensor.*_last_session_end` | Sensor | When the last session ended (timestamp) |
| `sensor.*_status_code` | Sensor | Raw charger status code (diagnostic) |

All grouped under a single **device** (`ABB Terra AC`).

## Installation

### HACS (recommended)
1. HACS → ⋮ → **Custom repositories**.
2. Add `https://github.com/Dviros/ha-abb-terra-ac` with category **Integration**.
3. Search for **ABB Terra AC (ChargerSync)**, install, and restart Home Assistant.

### Manual
Copy `custom_components/abb_charger/` into your Home Assistant `config/custom_components/` directory and
restart Home Assistant.

## Configuration

1. **Settings → Devices & Services → Add Integration → "ABB Terra AC (ChargerSync)"**.
2. Enter your **ChargerSync account email & password**. The charger is auto-discovered.

> [!TIP]
> ChargeDot allows **one active session per account**, so Home Assistant and the phone app will occasionally
> log each other out. Create a **separate ChargerSync account**, **share the charger to it**, and use that
> account here — Home Assistant then never disturbs your phone app.

## Notes & limitations

- **Cloud polling** (default 120 s) for status; commands are real-time over the cloud WebSocket.
- `status_code` is exposed raw while the enum is being mapped.
- Starting a session only delivers power if a vehicle is connected and requesting charge.

## Roadmap

- [ ] Live **charging / plugged / power** state (via the real-time status command)
- [ ] **Charging current** limit (number)
- [ ] **Free-vending**, **charge mode**, and **scheduled charging** controls
- [ ] Energy dashboard (total / cost) statistics

## Credits

Built with ❤️ for the Home Assistant community. Protocol reverse-engineered from the ChargerSync app for
personal interoperability with hardware the owner already controls.

## License

[MIT](LICENSE)
