import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Session
from django.utils import timezone

class StreamListener(AsyncWebsocketConsumer):
    async def connect(self):
        # Достаем ID сессии из URL (ws://127.0.0.1:8000/ws/stream/1/)
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f"stream_{self.session_id}"
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        # Обработка паузы
        if action == "pause":
            await self.set_session_paused()
            await self.channel_layer.group_send(
                self.room_group_name, {'type': 'broadcast', 'event': 'pause'}
            )
        # Обработка старта
        elif action == "play":
            await self.set_session_playing()
            await self.channel_layer.group_send(
                self.room_group_name, {'type': 'broadcast', 'event': 'play'}
            )
        # Обработка смены трека ведущим
        elif action == "change_track":
            await self.channel_layer.group_send(
                self.room_group_name, {'type': 'broadcast', 'event': 'change_track', 'url': data.get('url')}
            )

    # =========================================================
    # ВОТ ОНА - ТА САМАЯ ФУНКЦИЯ (ИЗ-ЗА КОТОРОЙ БЫЛА ОШИБКА)
    # =========================================================
    async def broadcast(self, event):
        payload = event.copy()
        
        # Переименовываем 'event' в 'event_type' для нашего JS в плеере
        if 'event' in payload:
            payload['event_type'] = payload.pop('event')
            
        # Удаляем служебный ключ 'type', он нужен был только для самого Django
        if 'type' in payload:
            del payload['type']
            
        # Отправляем JSON всем слушателям
        await self.send(text_data=json.dumps(payload))

    # --- Синхронные функции работы с БД ---
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