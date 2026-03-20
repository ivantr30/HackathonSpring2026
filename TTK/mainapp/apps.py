from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_roles(sender, **kwargs):
    from django.contrib.auth.models import Group 
    
    Group.objects.get_or_create(name='Слушатель')
    Group.objects.get_or_create(name='Ведущий')
    Group.objects.get_or_create(name='Админ')

class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainapp' 

    def ready(self):
        post_migrate.connect(create_default_roles, sender=self)