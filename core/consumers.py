import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import get_user
from channels.db import database_sync_to_async

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = await get_user(self.scope)

        if self.user.is_anonymous:
            print("❌ WebSocket rejected due to anonymous user.")
            await self.close()
        else:
            self.group_name = f"user_{self.user.id}"

            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            print(f"✅ WebSocket connected for user_{self.user.id}")

    async def disconnect(self, close_code):
        print(f"⚠️ WebSocket disconnected for user_{self.user.id}")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_notification",
                "message": data["message"],
            }
        )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({"message": event["message"]}))
