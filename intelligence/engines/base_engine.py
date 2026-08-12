"""
Base Engine
Common functionality for all intelligence engines
"""

from django.core.cache import cache
from django.db import models
from django.utils import timezone
from typing import Dict, Any, Optional, List
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class BaseEngine:
    """
    Base class for all intelligence engines with common utilities.
    """
    
    # Cache configuration
    CACHE_TIMEOUT = 3600  # 1 hour
    CACHE_PREFIX = 'engine_'
    
    @classmethod
    def get_cached(cls, key: str) -> Optional[Any]:
        """Get a value from cache."""
        return cache.get(f"{cls.CACHE_PREFIX}{key}")
    
    @classmethod
    def set_cached(cls, key: str, value: Any, timeout: int = None):
        """Set a value in cache."""
        cache.set(
            f"{cls.CACHE_PREFIX}{key}", 
            value, 
            timeout or cls.CACHE_TIMEOUT
        )
    
    @classmethod
    def invalidate_cache(cls, key: str = None):
        """Invalidate cache entries."""
        if key:
            cache.delete(f"{cls.CACHE_PREFIX}{key}")
        else:
            # Clear all engine cache
            cache.delete_pattern(f"{cls.CACHE_PREFIX}*")
    
    @staticmethod
    def calculate_decay_factor(days_since: int, half_life: int = 30) -> float:
        """
        Calculate decay factor using exponential decay.
        
        Args:
            days_since: Number of days since last activity
            half_life: Half-life in days
        
        Returns:
            Decay factor between 0 and 1
        """
        if days_since <= 0:
            return 1.0
        import math
        return math.exp(-days_since / half_life)
    
    @staticmethod
    def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Normalize a score to a range."""
        return max(min_val, min(max_val, score))
    
    @staticmethod
    def weighted_average(values: List[float], weights: List[float]) -> float:
        """Calculate weighted average."""
        if not values or not weights or len(values) != len(weights):
            return 0.0
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
            
        return sum(v * w for v, w in zip(values, weights)) / total_weight
    
    @staticmethod
    def calculate_consistency(scores: List[float]) -> float:
        """
        Calculate consistency from a list of scores.
        Higher consistency means less variance.
        """
        if len(scores) < 2:
            return 0.0
            
        import math
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = math.sqrt(variance)
        
        # Normalize: lower std_dev = higher consistency
        max_std_dev = 50.0  # Maximum possible standard deviation
        consistency = 1 - (std_dev / max_std_dev)
        
        return max(0.0, min(1.0, consistency))
    
    @staticmethod
    def get_recent_items(items, count: int = 5):
        """Get the most recent items from a list."""
        return sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)[:count]
