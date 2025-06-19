from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.trainers.models import Trainer, Organization

User = get_user_model()


class Command(BaseCommand):
    help = 'Create trainer profile for a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username to create trainer profile for'
        )
        parser.add_argument(
            '--role',
            type=str,
            default='trainer',
            choices=['owner', 'senior', 'trainer', 'assistant'],
            help='Role for the trainer'
        )
        parser.add_argument(
            '--organization',
            type=str,
            help='Organization slug (default: uses first available organization)'
        )

    def handle(self, *args, **options):
        username = options['username']
        role = options['role']
        org_slug = options.get('organization')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' does not exist"))
            return
            
        # Check if trainer profile already exists
        try:
            trainer = user.trainer_profile
            self.stdout.write(
                self.style.WARNING(
                    f"User '{username}' already has a trainer profile:\n"
                    f"  Organization: {trainer.organization.name if trainer.organization else 'None'}\n"
                    f"  Role: {trainer.get_role_display()}"
                )
            )
            return
        except Trainer.DoesNotExist:
            pass
            
        # Get organization
        if org_slug:
            try:
                organization = Organization.objects.get(slug=org_slug)
            except Organization.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Organization with slug '{org_slug}' does not exist"))
                return
        else:
            # Use first available organization
            organization = Organization.objects.first()
            if not organization:
                self.stdout.write(self.style.ERROR("No organizations exist. Creating default organization..."))
                organization = Organization.objects.create(
                    name='Default Organization',
                    slug='default',
                    max_trainers=50
                )
                
        # Create trainer profile
        trainer = Trainer.objects.create(
            user=user,
            organization=organization,
            role=role
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created trainer profile for '{username}':\n"
                f"  Organization: {organization.name}\n"
                f"  Role: {trainer.get_role_display()}"
            )
        )