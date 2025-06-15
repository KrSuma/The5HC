from django.utils.translation import gettext as _
from django.urls import reverse
from .models_notification import Notification


def notify_client_added(trainer, client):
    """
    Send notification when a new client is added.
    """
    # Notify the organization owner
    if trainer.organization:
        owners = trainer.organization.trainers.filter(role='owner', is_active=True)
        for owner in owners:
            if owner.user != trainer.user:  # Don't notify self
                Notification.create_notification(
                    user=owner.user,
                    notification_type='client_added',
                    title=_('New Client Added'),
                    message=_('%(trainer)s added a new client: %(client)s') % {
                        'trainer': trainer.get_display_name(),
                        'client': client.name
                    },
                    related_object_type='client',
                    related_object_id=client.id,
                    action_url=reverse('clients:detail', args=[client.id])
                )


def notify_assessment_completed(assessment):
    """
    Send notification when an assessment is completed.
    """
    client = assessment.client
    trainer = client.trainer
    
    # Notify organization seniors and owners
    if trainer.organization:
        supervisors = trainer.organization.trainers.filter(
            role__in=['owner', 'senior'], 
            is_active=True
        ).exclude(user=trainer.user)
        
        for supervisor in supervisors:
            Notification.create_notification(
                user=supervisor.user,
                notification_type='assessment_completed',
                title=_('Assessment Completed'),
                message=_('%(trainer)s completed an assessment for %(client)s (Score: %(score)s)') % {
                    'trainer': trainer.get_display_name(),
                    'client': client.name,
                    'score': assessment.overall_score or 'N/A'
                },
                related_object_type='assessment',
                related_object_id=assessment.id,
                action_url=reverse('assessments:detail', args=[assessment.id])
            )


def notify_payment_received(payment):
    """
    Send notification when a payment is received.
    """
    package = payment.session_package
    trainer = package.trainer
    
    # Notify the trainer
    Notification.create_notification(
        user=trainer.user,
        notification_type='payment_received',
        title=_('Payment Received'),
        message=_('Payment of ₩%(amount)s received for %(client)s') % {
            'amount': payment.amount,
            'client': package.client.name
        },
        related_object_type='payment',
        related_object_id=payment.id,
        action_url=reverse('sessions:package_detail', args=[package.id])
    )


def notify_trainer_invited(invitation):
    """
    Send notification when a trainer is invited.
    """
    # Notify all organization owners
    owners = invitation.organization.trainers.filter(role='owner', is_active=True)
    for owner in owners:
        if owner.user != invitation.invited_by:  # Don't notify self
            Notification.create_notification(
                user=owner.user,
                notification_type='trainer_invited',
                title=_('New Trainer Invitation'),
                message=_('%(inviter)s invited %(email)s to join as %(role)s') % {
                    'inviter': invitation.invited_by.get_full_name() or invitation.invited_by.email,
                    'email': invitation.email,
                    'role': invitation.get_role_display()
                },
                related_object_type='invitation',
                related_object_id=invitation.id,
                action_url=reverse('trainers:invite')
            )


def notify_trainer_joined(trainer):
    """
    Send notification when a trainer joins the organization.
    """
    # Notify all organization members
    org_members = trainer.organization.trainers.filter(
        is_active=True
    ).exclude(user=trainer.user)
    
    for member in org_members:
        Notification.create_notification(
            user=member.user,
            notification_type='trainer_joined',
            title=_('New Team Member'),
            message=_('%(name)s joined the organization as %(role)s') % {
                'name': trainer.get_display_name(),
                'role': trainer.get_role_display()
            },
            related_object_type='trainer',
            related_object_id=trainer.id,
            action_url=reverse('trainers:detail', args=[trainer.id])
        )


def notify_organization_update(organization, update_type, message):
    """
    Send notification for organization updates.
    """
    # Notify all organization members
    members = organization.trainers.filter(is_active=True)
    
    for member in members:
        Notification.create_notification(
            user=member.user,
            notification_type='organization_update',
            title=_('Organization Update'),
            message=message,
            related_object_type='organization',
            related_object_id=organization.id,
            action_url=reverse('trainers:organization_edit')
        )