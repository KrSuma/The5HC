"""
Caching layer for improved performance
"""
import time
import hashlib
import pickle
from typing import Any, Optional, Dict, Callable, Union, List
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock
import json

from app_logging import perf_logger, app_logger


class CacheEntry:
    """Represents a single cache entry"""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expiry_time = time.time() + ttl_seconds
        self.created_at = time.time()
        self.hit_count = 0
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > self.expiry_time
    
    def access(self) -> Any:
        """Access the cache entry and update stats"""
        self.hit_count += 1
        self.last_accessed = time.time()
        return self.value


class CacheStats:
    """Track cache statistics"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'expirations': self.expirations,
            'hit_rate': f"{self.hit_rate:.2f}%"
        }


class LRUCache:
    """Thread-safe LRU cache implementation"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.stats = CacheStats()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                if entry.is_expired():
                    # Remove expired entry
                    del self._cache[key]
                    self.stats.expirations += 1
                    self.stats.misses += 1
                    
                    perf_logger.logger.debug(f"Cache miss (expired): {key}")
                    return None
                
                # Move to end (most recently used)
                del self._cache[key]
                self._cache[key] = entry
                
                self.stats.hits += 1
                perf_logger.logger.debug(f"Cache hit: {key}")
                
                return entry.access()
            
            self.stats.misses += 1
            perf_logger.logger.debug(f"Cache miss: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        with self._lock:
            # Check if we need to evict
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Evict least recently used (first item)
                evict_key = next(iter(self._cache))
                del self._cache[evict_key]
                self.stats.evictions += 1
                perf_logger.logger.debug(f"Cache eviction: {evict_key}")
            
            # Add or update entry
            ttl_seconds = ttl or self.default_ttl
            self._cache[key] = CacheEntry(value, ttl_seconds)
            
            perf_logger.logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
    
    def invalidate(self, pattern: Optional[str] = None):
        """Invalidate cache entries"""
        with self._lock:
            if pattern:
                # Invalidate entries matching pattern
                keys_to_delete = [k for k in self._cache if pattern in k]
                for key in keys_to_delete:
                    del self._cache[key]
                    
                app_logger.info(f"Cache invalidated {len(keys_to_delete)} entries matching '{pattern}'")
            else:
                # Clear entire cache
                self._cache.clear()
                app_logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            stats = self.stats.to_dict()
            stats['size'] = len(self._cache)
            stats['max_size'] = self.max_size
            return stats


class CacheManager:
    """Manages multiple cache instances"""
    
    def __init__(self):
        # Different caches for different types of data
        self.caches = {
            'clients': LRUCache(max_size=500, default_ttl=600),  # 10 minutes
            'assessments': LRUCache(max_size=1000, default_ttl=300),  # 5 minutes
            'trainers': LRUCache(max_size=100, default_ttl=1800),  # 30 minutes
            'stats': LRUCache(max_size=200, default_ttl=60),  # 1 minute
            'queries': LRUCache(max_size=500, default_ttl=300)  # 5 minutes
        }
    
    def get_cache(self, cache_name: str) -> LRUCache:
        """Get specific cache instance"""
        if cache_name not in self.caches:
            # Create new cache if doesn't exist
            self.caches[cache_name] = LRUCache()
        return self.caches[cache_name]
    
    def invalidate_all(self):
        """Invalidate all caches"""
        for cache in self.caches.values():
            cache.invalidate()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        return {
            name: cache.get_stats() 
            for name, cache in self.caches.items()
        }


# Global cache manager
cache_manager = CacheManager()


# Cache key generators
def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    key_string = ":".join(key_parts)
    
    # Hash long keys
    if len(key_string) > 100:
        return hashlib.md5(key_string.encode()).hexdigest()
    
    return key_string


# Decorators for caching
def cached(cache_name: str = 'queries', ttl: Optional[int] = None, 
           key_prefix: Optional[str] = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_parts = [key_prefix or func.__name__]
            cache_key_parts.append(generate_cache_key(*args, **kwargs))
            cache_key = ":".join(cache_key_parts)
            
            # Try to get from cache
            cache = cache_manager.get_cache(cache_name)
            cached_value = cache.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Only cache if execution took significant time
            if execution_time > 10:  # 10ms threshold
                cache.set(cache_key, result, ttl)
            
            return result
            
        # Add cache management methods
        wrapper.invalidate = lambda: cache_manager.get_cache(cache_name).invalidate(
            key_prefix or func.__name__
        )
        
        return wrapper
    return decorator


def cache_aside(cache_name: str = 'queries', ttl: Optional[int] = None):
    """Cache-aside pattern decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key including instance info
            cache_key_parts = [
                func.__name__,
                self.__class__.__name__,
                generate_cache_key(*args, **kwargs)
            ]
            cache_key = ":".join(cache_key_parts)
            
            cache = cache_manager.get_cache(cache_name)
            
            # Try cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Load from source
            result = func(self, *args, **kwargs)
            
            # Store in cache
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
            
        return wrapper
    return decorator


# Specific cache implementations
class ClientCache:
    """Specialized cache for client data"""
    
    @staticmethod
    @cached(cache_name='clients', ttl=600)
    def get_client_list(trainer_id: int) -> List[Dict[str, Any]]:
        """Cache client list for trainer"""
        # This will be wrapped around the actual database call
        pass
    
    @staticmethod
    def invalidate_trainer_clients(trainer_id: int):
        """Invalidate client cache for specific trainer"""
        cache = cache_manager.get_cache('clients')
        cache.invalidate(f"get_client_list:{trainer_id}")


class AssessmentCache:
    """Specialized cache for assessment data"""
    
    @staticmethod
    @cached(cache_name='assessments', ttl=300)
    def get_assessment_details(assessment_id: int) -> Optional[Dict[str, Any]]:
        """Cache assessment details"""
        pass
    
    @staticmethod  
    @cached(cache_name='assessments', ttl=300)
    def get_client_assessments(client_id: int) -> List[Dict[str, Any]]:
        """Cache client assessment list"""
        pass
    
    @staticmethod
    def invalidate_client_assessments(client_id: int):
        """Invalidate assessment cache for specific client"""
        cache = cache_manager.get_cache('assessments')
        cache.invalidate(f"get_client_assessments:{client_id}")


class StatsCache:
    """Specialized cache for statistics"""
    
    @staticmethod
    @cached(cache_name='stats', ttl=60)
    def get_trainer_stats(trainer_id: int) -> Dict[str, Any]:
        """Cache trainer statistics"""
        pass
    
    @staticmethod
    @cached(cache_name='stats', ttl=120)
    def get_dashboard_metrics(trainer_id: int) -> Dict[str, Any]:
        """Cache dashboard metrics"""
        pass


# Cache warming strategies
class CacheWarmer:
    """Warm up caches with frequently accessed data"""
    
    @staticmethod
    def warm_trainer_cache(trainer_id: int):
        """Pre-load trainer-related data into cache"""
        try:
            # This would call the actual data loading functions
            # which are decorated with @cached
            app_logger.info(f"Warming cache for trainer {trainer_id}")
            
            # Example: Load trainer's clients
            # ClientService.get_trainer_clients(trainer_id)
            
            # Example: Load trainer stats  
            # DashboardService.get_trainer_stats(trainer_id)
            
        except Exception as e:
            app_logger.error(f"Cache warming failed: {e}")


# Cache monitoring
class CacheMonitor:
    """Monitor cache performance and health"""
    
    @staticmethod
    def log_cache_stats():
        """Log cache statistics"""
        stats = cache_manager.get_all_stats()
        
        for cache_name, cache_stats in stats.items():
            perf_logger.logger.info(
                f"Cache stats for '{cache_name}': {json.dumps(cache_stats)}"
            )
    
    @staticmethod
    def check_cache_health() -> Dict[str, Any]:
        """Check cache health metrics"""
        health = {
            'healthy': True,
            'caches': {}
        }
        
        for cache_name, cache in cache_manager.caches.items():
            cache_stats = cache.get_stats()
            
            cache_health = {
                'hit_rate': cache_stats['hit_rate'],
                'size': cache_stats['size'],
                'is_full': cache_stats['size'] >= cache_stats['max_size']
            }
            
            # Check if cache is performing poorly
            if float(cache_stats['hit_rate'].rstrip('%')) < 50 and cache_stats['hits'] > 100:
                cache_health['warning'] = 'Low hit rate'
                health['healthy'] = False
            
            health['caches'][cache_name] = cache_health
        
        return health


# Example usage in service layer
def cached_db_operation(operation: str, query_func: Callable, 
                       *args, ttl: int = 300, **kwargs) -> Any:
    """Generic cached database operation"""
    cache_key = f"{operation}:{generate_cache_key(*args, **kwargs)}"
    cache = cache_manager.get_cache('queries')
    
    # Check cache
    result = cache.get(cache_key)
    if result is not None:
        return result
    
    # Execute query
    result = query_func(*args, **kwargs)
    
    # Cache result
    if result is not None:
        cache.set(cache_key, result, ttl)
    
    return result