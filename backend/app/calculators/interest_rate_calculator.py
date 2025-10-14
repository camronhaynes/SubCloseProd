"""
Interest rate calculator for late interest calculations.
Handles both variable rates (e.g., Prime + spread) and flat rates.
Supports simple interest and various compounding periods.
"""

from datetime import date
from decimal import Decimal
from typing import List, Tuple, Optional
from ..models.data_models import PrimeRateChange, InterestCompounding


class InterestRateCalculator:
    """Calculates interest using either variable rates or a flat rate with configurable compounding"""

    def __init__(
        self,
        compounding: InterestCompounding,
        rate_history: Optional[List[PrimeRateChange]] = None,
        spread: Optional[Decimal] = None,
        flat_rate: Optional[Decimal] = None
    ):
        """
        Initialize calculator with either variable rates or flat rate.

        Args:
            compounding: Compounding method (simple, daily, monthly, quarterly, annual)
            rate_history: List of historical rate changes (for variable rates)
            spread: Percentage to add to base rate (e.g., 2 for 2%)
            flat_rate: Fixed rate percentage (e.g., 10 for 10%) - used if rate_history is None
        """
        self.compounding = compounding

        if flat_rate is not None:
            # Flat rate mode
            self.is_flat_rate = True
            self.flat_rate = flat_rate
            self.rate_history = None
            self.spread = Decimal('0')
        elif rate_history is not None:
            # Variable rate mode
            self.is_flat_rate = False
            self.rate_history = sorted(rate_history, key=lambda x: x.effective_date, reverse=True)
            self.spread = spread or Decimal('0')
            self.flat_rate = None
        else:
            raise ValueError("Must provide either rate_history or flat_rate")

    def get_rate_at_date(self, target_date: date) -> Decimal:
        """
        Get the effective rate on a specific date.

        Args:
            target_date: Date to lookup rate for

        Returns:
            Effective rate as percentage (base rate + spread for variable, or flat rate)
        """
        if self.is_flat_rate:
            return self.flat_rate

        # Variable rate: find applicable rate from history
        for rate_change in self.rate_history:
            if target_date >= rate_change.effective_date:
                return rate_change.rate + self.spread

        # If no rate found (date before all historical rates), use oldest rate
        if self.rate_history:
            return self.rate_history[-1].rate + self.spread

        raise ValueError("No rate history available")

    def _calculate_simple_interest(
        self,
        principal: Decimal,
        start_date: date,
        end_date: date
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate simple interest: I = P × r × t

        Uses inclusive day counting (adds +1) to match Excel convention:
        (end_date - start_date + 1) / 365

        Returns: (interest, effective_rate)
        """
        # Add +1 for inclusive day counting (Excel convention)
        total_days = (end_date - start_date).days + 1
        if total_days <= 0:
            return Decimal('0'), Decimal('0')

        if self.is_flat_rate:
            rate = self.flat_rate
            interest = principal * (rate / Decimal('100')) * (Decimal(total_days) / Decimal('365'))
            return interest, rate

        # Variable rate: segment by rate changes
        # Note: For variable rates with rate changes, we don't add +1 to segments,
        # only to the overall period for the weighted average calculation
        total_interest = Decimal('0')
        rate_changes_in_period = [
            rc for rc in self.rate_history
            if start_date < rc.effective_date <= end_date
        ]
        rate_changes_in_period.sort(key=lambda x: x.effective_date)

        current_date = start_date
        for rate_change in rate_changes_in_period:
            segment_days = (rate_change.effective_date - current_date).days
            if segment_days > 0:
                rate = self.get_rate_at_date(current_date)
                segment_interest = principal * (rate / Decimal('100')) * (Decimal(segment_days) / Decimal('365'))
                total_interest += segment_interest
            current_date = rate_change.effective_date

        # Final segment - add +1 here for inclusive counting
        final_days = (end_date - current_date).days + 1
        if final_days > 0:
            rate = self.get_rate_at_date(current_date)
            segment_interest = principal * (rate / Decimal('100')) * (Decimal(final_days) / Decimal('365'))
            total_interest += segment_interest

        # Weighted average rate
        weighted_avg_rate = (total_interest / principal) * (Decimal('365') / Decimal(total_days)) * Decimal('100')
        return total_interest, weighted_avg_rate

    def _calculate_compound_interest(
        self,
        principal: Decimal,
        start_date: date,
        end_date: date,
        compounding_frequency: str  # 'daily', 'monthly', 'quarterly', 'annual'
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate compound interest: A = P(1 + r/n)^(nt)
        where n = compounding periods per year, t = time in years

        Uses inclusive day counting (adds +1) to match Excel convention.
        For variable rates, compounds at each rate change boundary.

        Returns: (interest, effective_rate)
        """
        # Add +1 for inclusive day counting (Excel convention)
        total_days = (end_date - start_date).days + 1
        if total_days <= 0:
            return Decimal('0'), Decimal('0')

        # Map compounding frequency to periods per year
        periods_per_year = {
            'daily': 365,
            'monthly': 12,
            'quarterly': 4,
            'annual': 1
        }
        n = Decimal(periods_per_year[compounding_frequency])

        if self.is_flat_rate:
            # Simple compound calculation with flat rate
            rate = self.flat_rate / Decimal('100')  # Convert to decimal
            t = Decimal(total_days) / Decimal('365')  # Time in years

            # A = P(1 + r/n)^(nt)
            amount = principal * ((Decimal('1') + rate / n) ** (n * t))
            interest = amount - principal
            return interest, self.flat_rate

        # Variable rate: need to compound through each rate period
        current_balance = principal
        rate_changes_in_period = [
            rc for rc in self.rate_history
            if start_date < rc.effective_date <= end_date
        ]
        rate_changes_in_period.sort(key=lambda x: x.effective_date)

        current_date = start_date

        # Process each segment with its own rate
        for rate_change in rate_changes_in_period:
            segment_days = (rate_change.effective_date - current_date).days
            if segment_days > 0:
                rate = self.get_rate_at_date(current_date) / Decimal('100')
                t = Decimal(segment_days) / Decimal('365')
                current_balance = current_balance * ((Decimal('1') + rate / n) ** (n * t))
            current_date = rate_change.effective_date

        # Final segment - add +1 here for inclusive counting
        final_days = (end_date - current_date).days + 1
        if final_days > 0:
            rate = self.get_rate_at_date(current_date) / Decimal('100')
            t = Decimal(final_days) / Decimal('365')
            current_balance = current_balance * ((Decimal('1') + rate / n) ** (n * t))

        interest = current_balance - principal

        # Calculate effective annual rate
        t_total = Decimal(total_days) / Decimal('365')
        effective_rate = ((current_balance / principal) ** (Decimal('1') / t_total) - Decimal('1')) * Decimal('100')

        return interest, effective_rate

    def calculate_interest(
        self,
        principal: Decimal,
        start_date: date,
        end_date: date
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate interest over a period based on configured compounding method.

        Args:
            principal: Principal amount
            start_date: Start date of interest period
            end_date: End date of interest period

        Returns:
            Tuple of (total_interest, effective_rate_used)
        """
        if end_date < start_date:
            raise ValueError("End date must be after start date")

        if self.compounding == InterestCompounding.SIMPLE:
            return self._calculate_simple_interest(principal, start_date, end_date)
        else:
            # For MVP, we only support simple compounding
            # Compound interest would be added here
            # For now, compound defaults to daily compounding
            compounding_map = {
                InterestCompounding.COMPOUND: 'daily'  # Default to daily for compound
            }
            freq = compounding_map.get(self.compounding, 'daily')
            return self._calculate_compound_interest(principal, start_date, end_date, freq)
