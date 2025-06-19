from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.trainers.models import Trainer, Organization

User = get_user_model()


class Command(BaseCommand):
    help = 'Check and fix trainer profile issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to check/fix'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Create missing trainer profiles'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        fix = options.get('fix')

        if username:
            users = User.objects.filter(username=username)
        else:
            users = User.objects.filter(is_active=True)

        self.stdout.write(f"\nChecking {users.count()} users...\n")

        for user in users:
            try:
                trainer = user.trainer_profile
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {user.username} - Has trainer profile "
                        f"(Organization: {trainer.organization.name if trainer.organization else 'None'})"
                    )
                )
            except Trainer.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"✗ {user.username} - No trainer profile"
                    )
                )
                
                if fix:
                    # Get or create default organization
                    org, created = Organization.objects.get_or_create(
                        slug='default',
                        defaults={
                            'name': 'Default Organization',
                            'max_trainers': 50
                        }
                    )
                    
                    # Create trainer profile
                    trainer = Trainer.objects.create(
                        user=user,
                        organization=org,
                        role='trainer'
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  → Created trainer profile for {user.username}"
                        )
                    )

        # Show summary
        self.stdout.write("\n" + "="*50)
        total_users = users.count()
        users_with_profile = users.filter(trainer_profile__isnull=False).count()
        users_without_profile = total_users - users_with_profile
        
        self.stdout.write(f"Total users: {total_users}")
        self.stdout.write(f"With trainer profile: {users_with_profile}")
        self.stdout.write(f"Without trainer profile: {users_without_profile}")
        
        if users_without_profile > 0 and not fix:
            self.stdout.write(
                self.style.WARNING(
                    f"\nRun with --fix flag to create missing trainer profiles"
                )
            )