"""Async ChargeDot/ABB Terra AC cloud client (REST + plaintext WebSocket control)."""
from __future__ import annotations
import json, time, logging
from datetime import datetime, timedelta
import aiohttp
from yarl import URL

from .const import (REST, WS_HOST, WS_PORT, CLIENT_ID, CLIENT_SECRET, UA,
                    CMD_START, CMD_STOP, CMD_STATUS, CMD_IDENTITY, RESULT_CODES)

_LOGGER = logging.getLogger(__name__)
ACTION_CMD = {"start": (CMD_START, b"\x00\x00"), "stop": (CMD_STOP, b"\x00"), "status": (CMD_STATUS, b"\x00")}


def _des_ecb(data: bytes) -> bytes:
    """DES-ECB-PKCS5 with key 'ucserver' (TripleDES w/ 8-byte key == single DES)."""
    key = b"ucserver"
    pad = 8 - (len(data) % 8) or 8
    data = data + bytes([pad]) * pad
    try:
        from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
    except Exception:  # older cryptography
        from cryptography.hazmat.primitives.ciphers.algorithms import TripleDES
    from cryptography.hazmat.primitives.ciphers import Cipher, modes
    e = Cipher(TripleDES(key), modes.ECB()).encryptor()
    return e.update(data) + e.finalize()


def _wrap(cmd: int, body: bytes, token: bytes = bytes(8)) -> bytes:
    h = bytearray(8)
    h[0] = 0xFE; h[1] = cmd; h[4] = len(body) & 0xFF; h[5] = (len(body) >> 8) & 0xFF
    chk = 0
    for i in range(7):
        chk ^= h[i]
    for b in token + bytes(body):
        chk ^= b
    h[7] = chk & 0xFF
    return bytes(h) + token + bytes(body)


def _identity_frame(device_number: str, user_id: int) -> bytes:
    p = bytearray(48)
    dn = device_number.replace("-", "").encode()[:20]
    p[0:len(dn)] = dn
    p[20] = 2; p[21] = 1
    uid = str(user_id).encode()[:15]
    p[22:22 + len(uid)] = uid
    ct = _des_ecb(bytes(p))
    body = bytearray(130); body[0] = 0x80; body[2:2 + len(ct)] = ct
    return _wrap(CMD_IDENTITY, bytes(body))


class AbbChargeDotApi:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str):
        self._s = session
        self._user = username
        self._pw = password
        self._token = None
        self._token_exp = 0.0

    async def _oauth(self, force=False) -> str:
        if not force and self._token and self._token_exp > time.time() + 60:
            return self._token
        data = {"grant_type": "password", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
                "username": self._user, "password": self._pw}
        async with self._s.post(f"{REST}/api/oauth/token", data=data,
                                headers={"User-Agent": UA}) as r:
            j = await r.json()
            if r.status != 200 or "access_token" not in j:
                raise AuthError(f"login {r.status}: {json.dumps(j)[:120]}")
        self._token = j["access_token"]
        self._token_exp = time.time() + int(j.get("expires_in", 3600))
        return self._token

    def _hdr(self, tok):
        return {"Authorization": "Bearer " + tok, "x-app-platform": "iOS",
                "x-app-version": "3.4.0", "Accept-Language": "en", "User-Agent": UA}

    async def _get(self, path, force=False):
        for attempt in (1, 2):
            tok = await self._oauth(force=force or attempt == 2)
            async with self._s.get(f"{REST}{path}", headers=self._hdr(tok)) as r:
                if r.status == 401 and attempt == 1:
                    continue
                r.raise_for_status()
                return await r.json()
        raise AuthError(f"GET {path} unauthorized")

    async def _session_creds(self, force=False):
        me = await self._get("/api/v2/users/me", force=force)
        return me["sessionId"], me.get("authen", self._user), me["id"]

    async def get_devices(self):
        return await self._get("/api/v2/devices")

    async def get_device(self, device_id: int):
        return await self._get(f"/api/v2/devices/{device_id}")

    async def get_last_session(self, device_id: int):
        now = datetime.now()
        start = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        end = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            j = await self._get(
                f"/api/v2/devices/{device_id}/sessions?page=0&per_page=1&startTime={start}&endTime={end}")
        except Exception:
            return None
        items = j.get("data") if isinstance(j, dict) else j
        if isinstance(items, list) and items:
            return items[0]
        return None

    async def command(self, device_number: str, action: str) -> dict:
        """start|stop|status — returns {ok, result_code, result, raw}."""
        cmd, body = ACTION_CMD[action]
        last = {"ok": False, "error": "unknown"}
        for attempt in (1, 2):
            try:
                sid, email, uid = await self._session_creds(force=attempt == 2)
            except AuthError as e:
                return {"ok": False, "error": str(e)}
            url = URL(f"wss://{WS_HOST}:{WS_PORT}/ws/login?t={sid}&v=1&e={email}", encoded=True)
            try:
                async with self._s.ws_connect(url, headers={"User-Agent": UA}, heartbeat=25) as ws:
                    if not await self._await_login(ws):
                        last = {"ok": False, "error": "ws_login_rejected"}
                        continue  # refresh session + retry
                    idraw = await self._exchange(ws, device_number, _identity_frame(device_number, uid))
                    if not idraw or len(idraw) < 100:
                        return {"ok": False, "error": "identity_failed", "raw": idraw}
                    token = idraw[32:][52:68]
                    raw = await self._exchange(ws, device_number, _wrap(cmd, body, token=bytes.fromhex(token)))
                    if not raw or len(raw) < 6:
                        return {"ok": False, "error": "no_response", "raw": raw}
                    code = int(raw[4:6], 16)
                    return {"ok": code == 0, "result_code": code,
                            "result": RESULT_CODES.get(code, "unknown"), "raw": raw}
            except Exception as e:  # noqa
                last = {"ok": False, "error": repr(e)}
        return last

    async def _await_login(self, ws) -> bool:
        deadline = time.time() + 12
        while time.time() < deadline:
            msg = await ws.receive(timeout=12)
            if msg.type != aiohttp.WSMsgType.TEXT:
                return False
            if '"login"' in msg.data:
                return '"code":0' in msg.data.replace(" ", "")
        return False

    async def _exchange(self, ws, device_number: str, frame: bytes):
        await ws.send_str(json.dumps({"method": "remote_control", "to": device_number,
                                      "data": "".join(f"{b:02X}" for b in frame)}))
        deadline = time.time() + 12
        while time.time() < deadline:
            msg = await ws.receive(timeout=12)
            if msg.type != aiohttp.WSMsgType.TEXT:
                return None
            try:
                j = json.loads(msg.data)
            except Exception:
                continue
            if j.get("method") == "remote_control":
                return j.get("data", {}).get("raw")
        return None


class AuthError(Exception):
    pass
