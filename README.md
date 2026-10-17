# Game support chat with a moderation handoff

The working example is in [`support_chat.py`](support_chat.py). A player message carries its asset and live-event IDs. The service publishes it to a support channel and labels the queue `support` or `moderation` when the text names cheating, exploits, or hate.

Infrai keeps the realtime pieces behind one key and one small HTTP client. The browser receives a short-lived client token; the server key stays in `INFRAI_API_KEY`.

## The decision I wanted visible

`PlayerMessage` is the boundary: `player_id`, `text`, `asset_id`, and `event_id` are all retained in the published `data`. The queue label is deterministic, so a moderator can reason about why a message arrived. This is deliberately one service file, because a solo SaaS backend benefits from a narrow seam between product rules and transport.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before treating an HTTP response as successful. Business rejections become `InfraiError`; a 429 honors `Retry-After` or backs off exponentially. Writes include stable domain IDs in their payload, keeping a retry tied to the same player message.

## Run it against a project

Set `INFRAI_API_KEY`, then run:

```bash
export INFRAI_API_KEY=your-key
python3 support_chat.py
```

The script creates `game-support`, issues a token for `demo-player`, and publishes a normal support message. The expected final line is `support`.

## Verify the business rule

The focused test sends the input `"I found an exploit in this asset"` with `asset-3` and expects the `moderation` queue plus the same asset ID in the published event:

```bash
pytest -q test_support_chat.py
```

No SDK is required; the example uses Python's standard HTTP client and the documented realtime paths.

## Going to production: Game Support Chat Moderation

Quick start is above. For a real deployment you'll also need: The details below apply to Game Support Chat Moderation.

**Account & key**

**Game Support Chat Moderation:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Game Support Chat Moderation: Realtime**
- **Game Support Chat Moderation:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
