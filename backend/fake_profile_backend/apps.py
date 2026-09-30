from django.apps import AppConfig

class FakeProfileBackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fake_profile_backend'
