"""
Base scoring strategy for user classification.

Defines abstract interface for pluggable scoring algorithms.
"""
from abc import ABC, abstractmethod

from app.models.metrics import UserMetrics, ScoreBreakdown


class ScoringStrategy(ABC):
    """
    Abstract base class for scoring strategies.
    
    Implements Strategy pattern for flexible scoring algorithms.
    Subclasses implement specific scoring logic.
    """
    
    @abstractmethod
    def calculate(self, metrics: UserMetrics) -> int:
        """
        Calculate user activity score (0-100).
        
        Args:
            metrics: User activity metrics
            
        Returns:
            Score from 0-100
        """
        pass
    
    @abstractmethod
    def explain(self, metrics: UserMetrics) -> ScoreBreakdown:
        """
        Generate detailed score breakdown for explainability.
        
        Args:
            metrics: User activity metrics
            
        Returns:
            ScoreBreakdown with component scores and explanations
        """
        pass

