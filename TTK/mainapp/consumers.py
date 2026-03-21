import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Session, MediatekElement
from django.utils import timezone


class StreamListener(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f"stream_{self.session_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        state = await self.get_session_state()
        if state:
            await self.send(text_data=json.dumps({
                'event_type': 'sync',
                'state': state
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == "pause":
            await self.set_session_paused()
            state = await self.get_session_state()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_state',
                    'event_type': 'sync',
                    'state': state
                }
            )

        elif action == "play":
            await self.set_session_playing()
            state = await self.get_session_state()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_state',
                    'event_type': 'sync',
                    'state': state
                }
            )

        elif action == "change_track":
            track_id = data.get('track_id')
            await self.change_track_in_db(track_id)

            state = await self.get_session_state()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_state',
                    'event_type': 'sync',
                    'state': state
                }
            )

    async def broadcast(self, event):
        payload = event.copy()
        if 'event' in payload:
            payload['event_type'] = payload.pop('event')
        if 'type' in payload:
            del payload['type']
        await self.send(text_data=json.dumps(payload))

    async def broadcast_state(self, event):
        await self.send(text_data=json.dumps({
            'event_type': event['event_type'],
            'state': event['state']
        }))

    @database_sync_to_async
    def get_session_state(self):
        session = Session.objects.filter(id=self.session_id).first()
        if not session:
            return None

        state = session.get_state()
        current_track = state['current_track']

        return {
            'track_url': current_track.url() if current_track else "",
            'position': state['position'],
            'is_playing': state['is_playing']
        }

    @database_sync_to_async
    def change_track_in_db(self, track_id):
        session = Session.objects.filter(id=self.session_id).first()
        track = MediatekElement.objects.filter(id=track_id).first()
        if session and track:
            session.current_track = track
            session.current_track_paused_time = 0.0
            session.current_track_start_time = timezone.now()
            session.is_playing = True
            session.save()

    @database_sync_to_async
    def set_session_paused(self):
        user = self.scope['user']
        if user.is_authenticated:
            session = Session.objects.filter(id=self.session_id, owner=user).first()
            if session and session.is_playing:
                session.is_playing = False
                if session.current_track_start_time:
                    elapsed = (timezone.now() - session.current_track_start_time).total_seconds()
                    session.current_track_paused_time += elapsed
                session.save()

    @database_sync_to_async
    def set_session_playing(self):
        user = self.scope['user']
        if user.is_authenticated:
            session = Session.objects.filter(id=self.session_id, owner=user).first()
            if session and not session.is_playing:
                session.is_playing = True
                session.current_track_start_time = timezone.now()
                session.save()