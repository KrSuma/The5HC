"""
General utility functions
"""
import os
import shutil
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json


def format_date(date_str: str, format_from: str = "%Y-%m-%d", format_to: str = "%Y년 %m월 %d일") -> str:
    """Format date string"""
    try:
        date_obj = datetime.strptime(date_str, format_from)
        return date_obj.strftime(format_to)
    except ValueError:
        return date_str


def calculate_age_from_birth_date(birth_date: str) -> int:
    """Calculate age from birth date"""
    try:
        birth = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
            age -= 1
            
        return age
    except ValueError:
        return 0


def format_bmi_category(bmi: float) -> str:
    """Get BMI category"""
    if bmi < 18.5:
        return "저체중"
    elif bmi < 23:
        return "정상"
    elif bmi < 25:
        return "과체중"
    elif bmi < 30:
        return "비만 1단계"
    else:
        return "비만 2단계"


def format_fitness_level(score: float) -> str:
    """Get fitness level description"""
    if score >= 85:
        return "우수"
    elif score >= 70:
        return "양호"
    elif score >= 50:
        return "보통"
    else:
        return "주의필요"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def round_to_decimals(value: Optional[float], decimals: int = 1) -> Optional[float]:
    """Round to specified decimal places"""
    if value is None:
        return None
    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return None


def ensure_directory_exists(directory_path: str) -> bool:
    """Ensure directory exists, create if it doesn't"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except OSError:
        return False


def backup_file(file_path: str, backup_dir: str) -> Optional[str]:
    """Create backup of file"""
    try:
        if not os.path.exists(file_path):
            return None
            
        ensure_directory_exists(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_path = os.path.join(backup_dir, f"{filename}.backup_{timestamp}")
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception:
        return None


def clean_old_backups(backup_dir: str, keep_days: int = 30) -> int:
    """Clean old backup files"""
    if not os.path.exists(backup_dir):
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    cleaned_count = 0
    
    try:
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < cutoff_date:
                    os.remove(file_path)
                    cleaned_count += 1
                    
    except Exception:
        pass
    
    return cleaned_count


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def export_to_json(data: Dict[str, Any], file_path: str) -> bool:
    """Export data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception:
        return False


def import_from_json(file_path: str) -> Optional[Dict[str, Any]]:
    """Import data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def calculate_percentile(value: float, data_list: List[float]) -> float:
    """Calculate percentile of value in dataset"""
    if not data_list:
        return 0.0
    
    sorted_data = sorted(data_list)
    count_below = sum(1 for x in sorted_data if x < value)
    
    return (count_below / len(sorted_data)) * 100


def generate_summary_stats(values: List[float]) -> Dict[str, float]:
    """Generate summary statistics for a list of values"""
    if not values:
        return {
            'count': 0,
            'mean': 0.0,
            'median': 0.0,
            'min': 0.0,
            'max': 0.0,
            'std': 0.0
        }
    
    sorted_values = sorted(values)
    n = len(values)
    mean = sum(values) / n
    
    # Median
    if n % 2 == 0:
        median = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
    else:
        median = sorted_values[n//2]
    
    # Standard deviation
    variance = sum((x - mean) ** 2 for x in values) / n
    std = variance ** 0.5
    
    return {
        'count': n,
        'mean': round(mean, 2),
        'median': round(median, 2),
        'min': round(min(values), 2),
        'max': round(max(values), 2),
        'std': round(std, 2)
    }