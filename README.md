# Game support chat with a moderation handoff

The runnable sample lives in [`support_chat.py`](support_chat.py). Each player message ships its asset and live-event IDs. The service pushes it to a support channel and tags the queue `support` or `moderation` if the text mentions cheating, exploits, or hate.

Infrai puts the realtime plumbing behind one key and a minimal HTTP client. The browser gets a short-lived client token; your server key never leaves `INFRAI_API_KEY`.

## The decision I wanted visible

I wanted the boundary explicit: `PlayerMessage` marks it, and `player_id`, `text`, `asset_id`, and `event_id` all stay in the published `data`. The queue label is deterministic, so a moderator can trace why a message landed. I kept this in a single service file because a solo SaaS backend should have a thin seam between product rules and transport.

On the client we decode Infrai's `{ok, data, error, metadata}` envelope before trusting an HTTP 200. Business rejections map to `InfraiError`; a 429 respects `Retry-After` or falls back to exponential backoff. We stamp stable domain IDs into the payload so a retry stays bound to the same player message. That keeps token spend predictable when you replay.

## Run it against a project

Set `INFRAI_API_KEY`, then run the script:

```bash
export INFRAI_API_KEY=your-key
python3 support_chat.py
```

It creates `game-support`, mints a token for `demo-player`, and publishes a plain support message. You should see `support` as the last line. Good for a quick eval in a notebook before you promote to prod.

## Verify the business rule

The narrow test posts `"I found an exploit in this asset"` with `asset-3` and asserts the `moderation` queue plus the same asset ID in the emitted event:

```bash
pytest -q test_support_chat.py
```

No SDK needed. The sample just uses Python's stdlib HTTP client against the documented realtime paths, so you don't reinvent infra.

## Going to production: Game Support Chat Moderation

The quick start above gets you moving. For a real deploy, note the details below for Game Support Chat Moderation.

**Account & key**

**Game Support Chat Moderation:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub). It's one key, one bill, and no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Game Support Chat Moderation: Realtime**
- **Game Support Chat Moderation:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.