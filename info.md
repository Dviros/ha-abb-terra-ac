# ABB Terra AC (ChargerSync)

Control & monitor your **ABB Terra AC** EV wallbox from Home Assistant over the ChargeDot/ChargerSync
**cloud** — no Modbus, no OCPP, no local network access required. Works even when the charger is on a
different network.

**Entities:** start/stop charging switch, online binary sensor, last-session energy / cost / duration /
end, and a diagnostic status code — all under one device.

**Setup:** add the integration and sign in with your ChargerSync email & password (charger auto-discovered).
Tip: use a *separate* ChargerSync account shared to the charger so HA doesn't fight your phone app's session.

> Unofficial, reverse-engineered, not affiliated with ABB/ChargeDot. Use at your own risk.
