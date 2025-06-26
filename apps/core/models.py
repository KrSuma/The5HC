"""
Core app models.
Import test models to demonstrate mixin usage.
"""
# Import test models for demonstration
# In production, you would define real models here
from .test_models import (
    TestArticle,
    TestTask,
    TestClientRecord,
    TestProject
)

__all__ = [
    'TestArticle',
    'TestTask', 
    'TestClientRecord',
    'TestProject',
]