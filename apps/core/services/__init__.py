"""
Core services for The5HC application.

Services encapsulate business logic and provide a clean interface
between views and models. This promotes:
- Testability
- Reusability
- Separation of concerns
- Easier maintenance
"""

from .base import BaseService
from .client_service import ClientService
from .payment_service import PaymentService

__all__ = [
    'BaseService',
    'ClientService', 
    'PaymentService',
]