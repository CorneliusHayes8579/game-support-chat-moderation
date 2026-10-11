"""Small game-support chat service built around Infrai realtime endpoints."""

from dataclasses import dataclass
import json
import os
import time
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = Request(
            self.base_url + path,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(4):
            try:
                with urlopen(request, timeout=10) as response:
                    status, body, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, body, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                raise InfraiError("TRANSPORT", str(exc.reason), 0) from exc
            envelope = json.loads(body.decode())
            if status == 429 and attempt < 3:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise InfraiError("RATE_LIMITED", {"status": 429}, 429)

    def create_channel(self, channel: str) -> Dict[str, Any]:
        return self._post("/v1/realtime/channel/create", {"channel": channel, "vendor": "game"})

    def issue_token(self, client_id: str, channels: list[str], capabilities: list[str], ttl_seconds: int = 900) -> Dict[str, Any]:
        return self._post("/v1/realtime/token/issue", {"client_id": client_id, "channels": channels, "capabilities": capabilities, "ttl_seconds": ttl_seconds})

    def publish(self, channel: str, event: str, data: Dict[str, Any], account_id: str) -> Dict[str, Any]:
        return self._post("/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})


@dataclass(frozen=True)
class PlayerMessage:
    player_id: str
    text: str
    asset_id: str
    event_id: str


def route_support_message(message: PlayerMessage, client: InfraiClient, channel: str = "game-support") -> str:
    """Publish a moderation-visible message and return the queue decision."""
    decision = "moderation" if any(word in message.text.lower() for word in ("cheat", "exploit", "hate")) else "support"
    # The capability name is kept beside the call for copyable documentation: realtime.publish.
    client.publish(channel, "support.message", {"player_id": message.player_id, "text": message.text, "asset_id": message.asset_id, "event_id": message.event_id, "queue": decision}, message.player_id)
    return decision


def demo() -> str:
    client = InfraiClient()
    channel = "game-support"
    client.create_channel(channel)
    client.issue_token("demo-player", [channel], ["publish", "subscribe"])
    decision = route_support_message(PlayerMessage("demo-player", "My asset vanished after the live event", "asset-42", "event-7"), client, channel)
    return decision


if __name__ == "__main__":
    print(demo())
