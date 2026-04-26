"""
ROI and Savings Tracker Service.

Tracks baseline costs, actual savings, and calculates ROI metrics.
"""
import logging
from typing import List, Dict
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass

from app.models.db.savings_tracking import SavingsTracking, OptimizationAction
from app.events.event_bus import EventBus, Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class ROIMetrics:
    """ROI calculation metrics."""
    baseline_cost: Decimal
    current_cost: Decimal
    total_savings: Decimal
    monthly_savings: Decimal
    roi_percentage: float
    payback_period_months: float
    optimization_count: int


class SavingsTracker:
    """
    Service for tracking cost savings and ROI.
    
    Features:
    - Baseline cost management
    - Savings calculation
    - ROI metrics
    - Monthly/Annual reporting
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize savings tracker.
        
        Args:
            event_bus: Event bus for publishing savings events
        """
        self.event_bus = event_bus
    
    async def record_baseline(
        self,
        org_id: str,
        period: date,
        total_licenses: int,
        total_cost: Decimal
    ) -> SavingsTracking:
        """
        Record baseline costs.
        
        Args:
            org_id: Organization ID
            period: Baseline period
            total_licenses: Number of licenses
            total_cost: Total monthly cost
            
        Returns:
            SavingsTracking record
        """
        tracking = SavingsTracking(
            org_id=org_id,
            period=period,
            baseline_total_licenses=total_licenses,
            baseline_total_cost=total_cost,
            current_total_licenses=total_licenses,
            current_total_cost=total_cost,
            licenses_optimized=0,
            monthly_savings=Decimal("0"),
            cumulative_savings=Decimal("0")
        )
        
        logger.info(f"Baseline recorded for {org_id}: {total_licenses} licenses, ${total_cost}")
        
        return tracking
    
    async def record_optimization(
        self,
        tracking: SavingsTracking,
        action: OptimizationAction,
        licenses_affected: int,
        cost_savings: Decimal
    ) -> SavingsTracking:
        """
        Record an optimization action and update savings.
        
        Args:
            tracking: SavingsTracking record
            action: Type of optimization action
            licenses_affected: Number of licenses affected
            cost_savings: Cost savings from action
            
        Returns:
            Updated SavingsTracking
        """
        # Update tracking
        tracking.licenses_optimized += licenses_affected
        tracking.current_total_licenses -= licenses_affected
        tracking.monthly_savings += cost_savings
        tracking.cumulative_savings += cost_savings
        
        # Calculate new current cost
        tracking.current_total_cost = tracking.baseline_total_cost - tracking.monthly_savings
        
        logger.info(
            f"Optimization recorded: {action.value}, "
            f"{licenses_affected} licenses, ${cost_savings} savings"
        )
        
        # Publish event
        await self.event_bus.publish(Event(
            type=EventType.SAVINGS_ACHIEVED,
            data={
                "org_id": tracking.org_id,
                "action": action.value,
                "licenses": licenses_affected,
                "amount": float(cost_savings)
            }
        ))
        
        return tracking
    
    def calculate_roi(
        self,
        tracking: SavingsTracking,
        implementation_cost: Decimal = Decimal("0")
    ) -> ROIMetrics:
        """
        Calculate ROI metrics.
        
        Args:
            tracking: SavingsTracking record
            implementation_cost: One-time implementation cost
            
        Returns:
            ROIMetrics with calculated values
        """
        monthly_savings = tracking.monthly_savings
        annual_savings = monthly_savings * 12
        
        # Calculate ROI percentage
        if implementation_cost > 0:
            roi = float((annual_savings - implementation_cost) / implementation_cost * 100)
            payback_months = float(implementation_cost / monthly_savings) if monthly_savings > 0 else 0
        else:
            roi = 100.0  # Infinite ROI if no implementation cost
            payback_months = 0
        
        return ROIMetrics(
            baseline_cost=tracking.baseline_total_cost,
            current_cost=tracking.current_total_cost,
            total_savings=tracking.cumulative_savings,
            monthly_savings=monthly_savings,
            roi_percentage=roi,
            payback_period_months=payback_months,
            optimization_count=tracking.licenses_optimized
        )
    
    def generate_report(self, tracking: SavingsTracking) -> Dict:
        """
        Generate savings report.
        
        Args:
            tracking: SavingsTracking record
            
        Returns:
            Report dictionary
        """
        roi_metrics = self.calculate_roi(tracking)
        
        return {
            "period": tracking.period.isoformat(),
            "baseline": {
                "licenses": tracking.baseline_total_licenses,
                "monthly_cost": float(tracking.baseline_total_cost),
                "annual_cost": float(tracking.baseline_total_cost * 12)
            },
            "current": {
                "licenses": tracking.current_total_licenses,
                "monthly_cost": float(tracking.current_total_cost),
                "annual_cost": float(tracking.current_total_cost * 12)
            },
            "optimizations": {
                "licenses_optimized": tracking.licenses_optimized,
                "optimization_rate": float(tracking.licenses_optimized / tracking.baseline_total_licenses * 100)
            },
            "savings": {
                "monthly": float(roi_metrics.monthly_savings),
                "annual": float(roi_metrics.monthly_savings * 12),
                "cumulative": float(roi_metrics.total_savings)
            },
            "roi": {
                "percentage": roi_metrics.roi_percentage,
                "payback_period_months": roi_metrics.payback_period_months
            }
        }
    
    async def calculate_mrr(self, tracking: SavingsTracking) -> Decimal:
        """
        Calculate Monthly Recurring Revenue (MRR) impact.
        
        Args:
            tracking: SavingsTracking record
            
        Returns:
            MRR value
        """
        return tracking.monthly_savings
    
    async def calculate_ltv(
        self,
        tracking: SavingsTracking,
        months: int = 36
    ) -> Decimal:
        """
        Calculate Lifetime Value (LTV) of optimizations.
        
        Args:
            tracking: SavingsTracking record
            months: Time horizon in months
            
        Returns:
            LTV value
        """
        return tracking.monthly_savings * months


# Default instance
savings_tracker = SavingsTracker(event_bus=None)  # Will be injected
