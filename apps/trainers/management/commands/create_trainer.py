from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.trainers.models import Organization, Trainer


User = get_user_model()


class Command(BaseCommand):
    help = 'Create a new trainer account with organization assignment'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the trainer')
        parser.add_argument('email', type=str, help='Email address for the trainer')
        parser.add_argument('--password', type=str, default='testpass123', help='Password (default: testpass123)')
        parser.add_argument('--first-name', type=str, default='', help='First name')
        parser.add_argument('--last-name', type=str, default='', help='Last name')
        parser.add_argument('--organization', type=str, help='Organization slug (default: the5hc-fitness-center)')
        parser.add_argument('--role', type=str, choices=['owner', 'senior', 'trainer'], 
                          default='trainer', help='Trainer role (default: trainer)')
        parser.add_argument('--session-price', type=int, default=50000, 
                          help='Session price in KRW (default: 50000)')
        parser.add_argument('--is-staff', action='store_true', help='Give staff permissions')
        parser.add_argument('--is-superuser', action='store_true', help='Give superuser permissions')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        org_slug = options.get('organization', 'the5hc-fitness-center')
        role = options['role']
        session_price = options['session_price']
        is_staff = options['is_staff']
        is_superuser = options['is_superuser']

        try:
            with transaction.atomic():
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    raise CommandError(f'User with username "{username}" already exists')
                
                if User.objects.filter(email=email).exists():
                    raise CommandError(f'User with email "{email}" already exists')

                # Get organization
                try:
                    organization = Organization.objects.get(slug=org_slug)
                except Organization.DoesNotExist:
                    # List available organizations
                    orgs = Organization.objects.all()
                    org_list = '\n'.join([f'  - {o.name} (slug: {o.slug})' for o in orgs])
                    raise CommandError(
                        f'Organization with slug "{org_slug}" does not exist.\n'
                        f'Available organizations:\n{org_list}'
                    )

                # Check if organization can add more trainers
                if not organization.can_add_trainer():
                    raise CommandError(
                        f'Organization "{organization.name}" has reached its maximum '
                        f'trainer limit ({organization.max_trainers})'
                    )

                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_staff,
                    is_superuser=is_superuser
                )
                user.name = f"{first_name} {last_name}".strip() or username
                user.save()

                # Create trainer profile
                trainer = Trainer.objects.create(
                    user=user,
                    organization=organization,
                    role=role,
                    session_price=session_price,
                    is_active=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created trainer:\n'
                        f'  Username: {username}\n'
                        f'  Email: {email}\n'
                        f'  Name: {user.get_full_name() or username}\n'
                        f'  Organization: {organization.name}\n'
                        f'  Role: {trainer.get_role_display()}\n'
                        f'  Session Price: ₩{session_price:,}\n'
                        f'  Staff: {is_staff}\n'
                        f'  Superuser: {is_superuser}'
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating trainer: {str(e)}'))
            raise