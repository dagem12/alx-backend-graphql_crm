import os
from celery import Celery
from django.conf import settings

# Définir le module de paramètres par défaut pour l'application Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

# Créer une instance de l'application Celery
app = Celery('crm')

# Utiliser les paramètres de configuration de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans les applications Django
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configuration pour utiliser Redis comme broker
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'

# Configuration du fuseau horaire
app.conf.timezone = 'Europe/Paris'
