import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'live_stream'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Рассылаем команду всем в комнате
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'stream_event',
                'event_type': data['event_type'],
                'payload': data.get('payload', {})
            }
        )

    async def stream_event(self, event):
        await self.send(text_data=json.dumps({
            'event_type': event['event_type'],
            'payload': event['payload']
        }))