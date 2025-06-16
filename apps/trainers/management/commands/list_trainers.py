from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.trainers.models import Organization, Trainer


class Command(BaseCommand):
    help = 'List all organizations and trainers in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=str,
            help='Filter by organization slug'
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['owner', 'senior', 'trainer'],
            help='Filter by trainer role'
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Show only active trainers'
        )

    def handle(self, *args, **options):
        org_filter = options.get('organization')
        role_filter = options.get('role')
        active_only = options.get('active_only', False)

        # List organizations
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== ORGANIZATIONS ===\n'))
        
        orgs = Organization.objects.annotate(
            trainer_count=Count('trainers', filter=models.Q(trainers__is_active=True))
        )
        
        if org_filter:
            orgs = orgs.filter(slug=org_filter)
        
        for org in orgs:
            self.stdout.write(
                f"{self.style.SUCCESS(org.name)} (slug: {org.slug})\n"
                f"  Trainers: {org.trainer_count}/{org.max_trainers}\n"
                f"  Email: {org.email or 'N/A'}\n"
                f"  Phone: {org.phone or 'N/A'}\n"
            )
        
        # List trainers
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== TRAINERS ===\n'))
        
        trainers = Trainer.objects.select_related('user', 'organization').order_by(
            'organization__name', 'role', 'user__username'
        )
        
        if org_filter:
            trainers = trainers.filter(organization__slug=org_filter)
        
        if role_filter:
            trainers = trainers.filter(role=role_filter)
        
        if active_only:
            trainers = trainers.filter(is_active=True)
        
        current_org = None
        for trainer in trainers:
            # Print organization header when it changes
            if current_org != trainer.organization:
                current_org = trainer.organization
                self.stdout.write(f"\n{self.style.WARNING(current_org.name)}:")
            
            # Format trainer info
            status = self.style.SUCCESS('Active') if trainer.is_active else self.style.ERROR('Inactive')
            role_display = self.style.NOTICE(f'[{trainer.get_role_display()}]')
            
            self.stdout.write(
                f"  {trainer.user.username} {role_display} - "
                f"{trainer.get_display_name()} ({trainer.user.email}) - {status}"
            )
            
            # Show additional info
            if trainer.session_price:
                self.stdout.write(f"    Session Price: ₩{trainer.session_price:,}")
            if trainer.years_of_experience:
                self.stdout.write(f"    Experience: {trainer.years_of_experience} years")
            if trainer.specialties:
                self.stdout.write(f"    Specialties: {', '.join(trainer.specialties)}")
        
        # Summary
        total_trainers = trainers.count()
        active_trainers = trainers.filter(is_active=True).count()
        
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n=== SUMMARY ===\n'
            f'Total Organizations: {orgs.count()}\n'
            f'Total Trainers: {total_trainers} ({active_trainers} active)\n'
        ))


# Fix the import
from django.db import models