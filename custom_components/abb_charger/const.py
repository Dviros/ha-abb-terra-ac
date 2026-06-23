DOMAIN = "abb_charger"

REST = "https://abb-user.chargedot.com"
WS_HOST = "abb.api.chargedot.com"
WS_PORT = 18971
CLIENT_ID = "3710400e-1c02-4175-84ea-40a227c0dcf6"
CLIENT_SECRET = "f1a6d022-8a8e-453c-862e-ba0d3c5b4521"
UA = "ChargerSync/3.4.0 (com.abb-e-mobility.chargersync; build:1915.551; iOS 26.5.0) Alamofire/5.8.0"

# command opcodes
CMD_START = 0xB4
CMD_STOP = 0xB6
CMD_STATUS = 0xB5
CMD_IDENTITY = 0xFE
CMD_POWER_CONTROL = 0xC0  # set charging current / load balancing; body = [port(0), outputCurrent]

MIN_CHARGE_CURRENT = 6  # IEC 61851 AC minimum

RESULT_CODES = {
    0: "success", 17: "parse_error", 18: "no_permission", 19: "reject",
    20: "cmd_not_exist", 21: "cmd_not_support", 22: "token_timeout",
    80: "device_error", 81: "cmd_execute_failure",
}

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_NUMBER = "device_number"

SCAN_INTERVAL_SECONDS = 60
