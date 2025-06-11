"""
Basic test to verify pytest setup is working.
"""
import pytest


def test_basic_math():
    """Test basic math operations"""
    assert 2 + 2 == 4
    assert 3 * 3 == 9
    assert 10 / 2 == 5.0


class TestBasicClass:
    """Test basic class functionality"""
    
    def test_string_operations(self):
        """Test string operations"""
        text = "Hello World"
        assert text.lower() == "hello world"
        assert text.upper() == "HELLO WORLD"
        assert len(text) == 11
    
    def test_list_operations(self):
        """Test list operations"""
        items = [1, 2, 3, 4, 5]
        assert len(items) == 5
        assert sum(items) == 15
        assert max(items) == 5


@pytest.mark.parametrize('input_val,expected', [
    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8),
])
def test_double_values(input_val, expected):
    """Test parametrized doubling function"""
    assert input_val * 2 == expected