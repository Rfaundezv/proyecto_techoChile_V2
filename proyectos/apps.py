
from django.apps import AppConfig

class ProyectosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'proyectos'
    verbose_name = 'Gestión de Proyectos'
    
    def ready(self):
        """Registrar signals cuando la app está lista"""
        import proyectos.models  # Importar para activar los signals
