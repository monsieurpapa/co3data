import json
from django.core.management.base import BaseCommand
from users.models import User
from cooperatives.models import Cooperative


class Command(BaseCommand):
    help = 'Populate user accounts from a JSON file.'

    def add_arguments(self, parser):
        parser.add_argument('path', help='Path to JSON file containing a list of users')

    def handle(self, *args, **options):
        path = options['path']
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stderr.write(f'Unable to open JSON file: {e}')
            return

        if not isinstance(data, list):
            self.stderr.write('JSON payload must be a list of user objects')
            return

        for item in data:
            username = item.get('username')
            if not username:
                self.stderr.write('Skipping user entry without username')
                continue

            user, created = User.objects.get_or_create(username=username)
            # basic fields
            user.email = item.get('email', '')
            if item.get('first_name'):
                user.first_name = item['first_name']
            if item.get('last_name'):
                user.last_name = item['last_name']
            pw = item.get('password')
            if pw:
                user.set_password(pw)
            user.is_staff = item.get('is_staff', False)
            user.is_active = item.get('is_active', True)
            
            # Map role
            role_value = item.get('role')
            if role_value:
                user.role = role_value
            
            # Add cooperative if provided
            coop_value = item.get('cooperative') or item.get('organization')
            if coop_value:
                try:
                    if isinstance(coop_value, int):
                        coop = Cooperative.objects.get(pk=coop_value)
                    else:
                        coop = Cooperative.objects.get(name=coop_value)
                    user.cooperative = coop
                except Cooperative.DoesNotExist:
                    self.stderr.write(f'Cooperative "{coop_value}" not found for user {username}')

            user.save()
            self.stdout.write(f'{"Created" if created else "Updated"} user {username}')
