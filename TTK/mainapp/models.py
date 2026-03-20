from django.db import models
from django.core.validators import FileExtensionValidator, RegexValidator
from django.conf import settings
from django.contrib.auth.models import AbstractUser 
from django.core.exceptions import ValidationError

# Create your models here.
# Роли реализованны через django groups, пример в admin.py
# 2 ВАЛИДАТОРА НИЖЕ РАБОТАЮТ ТОЛЬКО ПРИ ВЫЗОВЕ full-clean() при сохранении формы!!!!
def validate_video_size(value):
    limit_mb = 1000
    if value.size > limit_mb * 1024 * 1024:
        raise ValidationError(f'Файл слишком большой! Максимум {limit_mb} МБ.')
    
def validate_audio_size(value):
    limit_mb = 50
    if value.size > limit_mb * 1024 * 1024:
        raise ValidationError(f'Файл слишком большой! Максимум {limit_mb} МБ.')
     
class User(AbstractUser):
    username = models.CharField(
        max_length=35, 
        unique=True, 
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z]+$', 
            )
        ]
    )
    fullName = models.CharField(max_length=100, verbose_name="ФИО", validators=[RegexValidator(regex=r'^[[А-Яа-яЁё\s-]+$',)])
    def __str__(self):
        return self.username[:20]
    
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receivedmessages')
    text = models.TextField()
    def __str__(self):
        return self.text
class VoiceMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voices')
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receivedvoices')
    voice_message = models.FileField(
        upload_to='voice/', 
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'ogg'])],
    )
    def __str__(self):
        return self.sender.__str__()
class MediatekElement(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mediatekelements')
    name = models.CharField(max_length=100)

class Playlist(models.Model):
    title = models.CharField(max_length=100)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playlists')
    elements = models.ManyToManyField(MediatekElement, related_name='playlists', blank=True)
    
class Audio(MediatekElement):
    audio_file = models.FileField(
        upload_to='audio/', 
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'ogg']), validate_audio_size],
    )
class Video(MediatekElement):
    video_file = models.FileField(
        upload_to='video/', 
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm']), validate_video_size],
    )
