from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Promote all users in the ADMINISTRADOR group to superuser status'

    def handle(self, *args, **options):
        try:
            group = Group.objects.get(name='ADMINISTRADOR')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR("El grupo 'ADMINISTRADOR' no existe."))
            return

        users = group.user_set.all()
        if not users:
            self.stdout.write(self.style.WARNING("No hay usuarios en el grupo 'ADMINISTRADOR'."))
            return

        for user in users:
            if not user.is_superuser:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Usuario '{user.email}' promovido a superusuario."))
            else:
                self.stdout.write(f"Usuario '{user.email}' ya es superusuario.")

        self.stdout.write(self.style.SUCCESS('Promoción completada.'))