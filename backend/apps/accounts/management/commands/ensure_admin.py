from decouple import config
from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Cria o superusuário padrão (ADMIN_EMAIL/ADMIN_PASSWORD) se ele ainda não existir.'

    def handle(self, *args, **options):
        email = config('ADMIN_EMAIL', default='')
        password = config('ADMIN_PASSWORD', default='')

        if not email or not password:
            self.stdout.write('ADMIN_EMAIL/ADMIN_PASSWORD não definidos, pulando.')
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(f'usuário {email} já existe, pulando.')
            return

        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'superusuário {email} criado.'))
