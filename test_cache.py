"""
Tests for caching and performance improvements
"""
import pytest
import time
from unittest.mock import Mock, patch
from cache import (
    CacheEntry, LRUCache, CacheManager, 
    cached, cache_aside, generate_cache_key
)


class TestCacheEntry:
    """Test cache entry functionality"""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation and expiry"""
        entry = CacheEntry(value="test_value", ttl_seconds=1)
        
        assert entry.value == "test_value"
        assert entry.hit_count == 0
        assert not entry.is_expired()
        
        # Access the entry
        value = entry.access()
        assert value == "test_value"
        assert entry.hit_count == 1
        
        # Test expiry
        time.sleep(1.1)
        assert entry.is_expired()


class TestLRUCache:
    """Test LRU cache implementation"""
    
    def test_basic_cache_operations(self):
        """Test basic get/set operations"""
        cache = LRUCache(max_size=3, default_ttl=60)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.stats.hits == 1
        assert cache.stats.misses == 0
        
        # Test miss
        assert cache.get("nonexistent") is None
        assert cache.stats.misses == 1
    
    def test_cache_eviction(self):
        """Test LRU eviction policy"""
        cache = LRUCache(max_size=3, default_ttl=60)
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it most recently used
        cache.get("key1")
        
        # Add new item, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still present
        assert cache.get("key2") is None      # Evicted
        assert cache.get("key3") == "value3"  # Still present
        assert cache.get("key4") == "value4"  # New item
        assert cache.stats.evictions == 1
    
    def test_cache_expiry(self):
        """Test cache entry expiration"""
        cache = LRUCache(max_size=10, default_ttl=1)
        
        # Set with short TTL
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        
        # Wait for expiry
        time.sleep(1.1)
        assert cache.get("key1") is None
        assert cache.stats.expirations == 1
    
    def test_cache_invalidation(self):
        """Test cache invalidation"""
        cache = LRUCache(max_size=10, default_ttl=60)
        
        # Add multiple entries
        cache.set("user:1", "data1")
        cache.set("user:2", "data2")
        cache.set("admin:1", "data3")
        
        # Invalidate by pattern
        cache.invalidate("user:")
        
        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("admin:1") == "data3"  # Not invalidated
        
        # Clear all
        cache.invalidate()
        assert cache.get("admin:1") is None


class TestCacheDecorators:
    """Test caching decorators"""
    
    def test_cached_decorator(self):
        """Test @cached decorator"""
        call_count = 0
        
        @cached(cache_name='test', ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call - cache miss
        result = expensive_function(1, 2)
        assert result == 3
        assert call_count == 1
        
        # Second call - cache hit
        result = expensive_function(1, 2)
        assert result == 3
        assert call_count == 1  # Function not called again
        
        # Different arguments - cache miss
        result = expensive_function(2, 3)
        assert result == 5
        assert call_count == 2
    
    def test_cache_aside_decorator(self):
        """Test @cache_aside decorator"""
        class TestRepository:
            call_count = 0
            
            @cache_aside(cache_name='test', ttl=60)
            def get_data(self, id):
                self.call_count += 1
                return f"data_{id}"
        
        repo = TestRepository()
        
        # First call - cache miss
        result = repo.get_data(1)
        assert result == "data_1"
        assert repo.call_count == 1
        
        # Second call - cache hit
        result = repo.get_data(1)
        assert result == "data_1"
        assert repo.call_count == 1  # Method not called again


class TestCacheKeyGeneration:
    """Test cache key generation"""
    
    def test_simple_key_generation(self):
        """Test simple cache key generation"""
        key = generate_cache_key(1, 2, 3)
        assert key == "1:2:3"
        
        key = generate_cache_key(user_id=1, page=2)
        assert key == "page=2:user_id=1"  # Sorted by key
    
    def test_long_key_hashing(self):
        """Test that long keys are hashed"""
        # Create a long key
        long_arg = "x" * 200
        key = generate_cache_key(long_arg)
        
        # Should be hashed (MD5 = 32 chars)
        assert len(key) == 32


class TestCacheManager:
    """Test cache manager"""
    
    def test_multiple_caches(self):
        """Test managing multiple cache instances"""
        manager = CacheManager()
        
        # Get different caches
        client_cache = manager.get_cache('clients')
        assessment_cache = manager.get_cache('assessments')
        
        # They should be different instances
        assert client_cache is not assessment_cache
        
        # Set in one cache
        client_cache.set("test", "value")
        
        # Should not affect other cache
        assert assessment_cache.get("test") is None
    
    def test_get_all_stats(self):
        """Test getting stats for all caches"""
        manager = CacheManager()
        
        # Use some caches
        manager.get_cache('clients').set("key1", "value1")
        manager.get_cache('clients').get("key1")
        manager.get_cache('assessments').set("key2", "value2")
        
        stats = manager.get_all_stats()
        
        assert 'clients' in stats
        assert 'assessments' in stats
        assert stats['clients']['hits'] == 1
        assert stats['clients']['size'] == 1


class TestPerformanceImprovement:
    """Test actual performance improvements with caching"""
    
    def test_database_query_caching(self):
        """Test that database queries are cached"""
        # Mock database function
        mock_db_call = Mock(return_value=[{"id": 1, "name": "Test"}])
        
        @cached(cache_name='queries', ttl=60)
        def get_clients(trainer_id):
            return mock_db_call(trainer_id)
        
        # First call
        result1 = get_clients(1)
        assert mock_db_call.call_count == 1
        
        # Second call - should use cache
        result2 = get_clients(1)
        assert mock_db_call.call_count == 1  # Not called again
        assert result1 == result2
        
        # Different parameter - new call
        result3 = get_clients(2)
        assert mock_db_call.call_count == 2
    
    def test_cache_performance_metrics(self):
        """Test cache performance tracking"""
        cache = LRUCache(max_size=100, default_ttl=60)
        
        # Simulate usage
        for i in range(50):
            cache.set(f"key{i}", f"value{i}")
        
        # Simulate hits and misses
        for i in range(30):  # 30 hits
            cache.get(f"key{i}")
        
        for i in range(50, 70):  # 20 misses
            cache.get(f"key{i}")
        
        stats = cache.get_stats()
        assert stats['hits'] == 30
        assert stats['misses'] == 20
        assert float(stats['hit_rate'].rstrip('%')) == 60.0  # 30/(30+20) * 100


class TestCacheIntegration:
    """Integration tests for caching with services"""
    
    @patch('improved_service_layer.db_get_clients')
    def test_service_layer_caching(self, mock_get_clients):
        """Test that service layer uses caching effectively"""
        from services import ClientService
        
        mock_get_clients.return_value = [(1, "Client 1"), (2, "Client 2")]
        
        # Clear any existing cache
        cache_manager.invalidate_all()
        
        # First call - should hit database
        result1 = ClientService.get_trainer_clients(1)
        assert mock_get_clients.call_count == 1
        
        # Second call - should use cache
        result2 = ClientService.get_trainer_clients(1)
        assert mock_get_clients.call_count == 1  # No additional call
        assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])