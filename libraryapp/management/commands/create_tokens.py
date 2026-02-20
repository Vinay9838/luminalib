from django.core.management.base import BaseCommand, CommandError

from libraryapp.auth_service import TokenService

class Command(BaseCommand):
    help = 'Create a JWT token for a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the token')
        parser.add_argument('client_name', type=str, help='Client name for the token')

    def handle(self, *args, **options):
        username = options['username']
        client_name = options['client_name']
        token_service = TokenService()
        try:
            token = token_service.create_token(username=username, client_name=client_name)
        except Exception as e:
            raise CommandError(f'Error creating token: {e}')
        self.stdout.write(self.style.SUCCESS(f'Token created: {token}'))