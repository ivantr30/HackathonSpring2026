import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StreamListener(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "some_room"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        await self.channel_layer.group_send(
            self.room_name,
            {
                'type' : 'broadcast_message',
                'text' : message,
            }
        )
    async def broadcast_message(self, event):
        await self.send(text_data=json.dumps({
            'server' : event['text']
        }))
    