from support_chat import PlayerMessage, route_support_message


class RecordingClient:
    def __init__(self):
        self.calls = []

    def publish(self, channel, event, data, account_id):
        self.calls.append((channel, event, data, account_id))
        return {"ok": True, "data": {}}


def test_asset_exploit_message_enters_moderation_queue():
    client = RecordingClient()
    message = PlayerMessage("p-9", "I found an exploit in this asset", "asset-3", "event-2")
    result = route_support_message(message, client)
    assert result == "moderation"
    assert client.calls[0][2]["queue"] == "moderation"
    assert client.calls[0][2]["asset_id"] == "asset-3"
