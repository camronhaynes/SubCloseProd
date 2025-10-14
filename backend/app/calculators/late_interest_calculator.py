"""
Late interest calculator for new LPs joining at subsequent closes.
Handles business logic of determining what capital calls were missed
and calculating late interest owed on each.
"""

from datetime import date
from decimal import Decimal
from typing import List
from ..models.data_models import (
    Partner,
    CapitalCall,
    FundAssumptions,
    NewLPCalculation,
    LateInterestDetail,
    EndDateCalculation
)
from .interest_rate_calculator import InterestRateCalculator


class LateInterestCalculator:
    """Calculates late interest owed by new LPs for missed capital calls"""

    def __init__(self, assumptions: FundAssumptions):
        """
        Initialize with fund configuration.

        Args:
            assumptions: Fund-level calculation assumptions
        """
        self.assumptions = assumptions

        # Initialize interest rate calculator based on fund settings
        if assumptions.late_interest_base.value == 'prime':
            self.rate_calculator = InterestRateCalculator(
                compounding=assumptions.late_interest_compounding,
                rate_history=assumptions.prime_rate_history,
                spread=assumptions.late_spread
            )
        else:  # flat rate
            self.rate_calculator = InterestRateCalculator(
                compounding=assumptions.late_interest_compounding,
                flat_rate=assumptions.flat_rate
            )

    def calculate_late_interest_for_new_lp(
        self,
        new_lp: Partner,
        capital_calls: List[CapitalCall]
    ) -> NewLPCalculation:
        """
        Calculate total late interest owed by a new LP.

        Args:
            new_lp: The new LP joining the fund
            capital_calls: All capital calls that occurred before LP admission

        Returns:
            Complete calculation breakdown with totals
        """
        # Filter to capital calls that occurred before LP admission
        missed_calls = [
            call for call in capital_calls
            if call.due_date < new_lp.issue_date
        ]

        # Sort by call number for consistent output
        missed_calls.sort(key=lambda x: x.call_number)

        breakdown = []
        total_catch_up = Decimal('0')
        total_late_interest = Decimal('0')

        for call in missed_calls:
            detail = self._calculate_late_interest_for_call(new_lp, call)
            breakdown.append(detail)
            total_catch_up += detail.capital_amount
            total_late_interest += detail.late_interest

        # Round totals according to fund settings
        total_catch_up = self._round_amount(total_catch_up, self.assumptions.sum_rounding)
        total_late_interest = self._round_amount(total_late_interest, self.assumptions.sum_rounding)

        return NewLPCalculation(
            partner_name=new_lp.name,
            issue_date=new_lp.issue_date,
            commitment=new_lp.commitment,
            close_number=new_lp.close_number,
            total_catch_up=total_catch_up,
            total_late_interest_due=total_late_interest,
            breakdown_by_capital_call=breakdown
        )

    def _calculate_late_interest_for_call(
        self,
        new_lp: Partner,
        call: CapitalCall
    ) -> LateInterestDetail:
        """
        Calculate late interest for a single capital call.

        Args:
            new_lp: The new LP
            call: The capital call

        Returns:
            Late interest detail for this call
        """
        # Calculate capital amount owed
        capital_amount = call.get_call_amount(new_lp.commitment)

        # Determine end date for interest calculation
        if self.assumptions.end_date_calculation == EndDateCalculation.ISSUE_DATE:
            end_date = new_lp.issue_date
        else:  # DUE_DATE
            end_date = call.due_date

        # Calculate days late
        days_late = (end_date - call.due_date).days

        if days_late <= 0:
            # No late interest if not actually late
            return LateInterestDetail(
                call_number=call.call_number,
                due_date=call.due_date,
                call_percentage=call.call_percentage,
                capital_amount=capital_amount,
                late_interest=Decimal('0'),
                days_late=0,
                effective_rate=Decimal('0')
            )

        # Calculate late interest using interest rate calculator
        late_interest, effective_rate = self.rate_calculator.calculate_interest(
            principal=capital_amount,
            start_date=call.due_date,
            end_date=end_date
        )

        # Round according to fund settings
        late_interest = self._round_amount(late_interest, self.assumptions.calc_rounding)
        effective_rate = self._round_amount(effective_rate, self.assumptions.calc_rounding)
        capital_amount = self._round_amount(capital_amount, self.assumptions.calc_rounding)

        return LateInterestDetail(
            call_number=call.call_number,
            due_date=call.due_date,
            call_percentage=call.call_percentage,
            capital_amount=capital_amount,
            late_interest=late_interest,
            days_late=days_late,
            effective_rate=effective_rate
        )

    def _round_amount(self, amount: Decimal, decimal_places: int) -> Decimal:
        """
        Round a decimal amount to specified decimal places.

        Args:
            amount: Amount to round
            decimal_places: Number of decimal places

        Returns:
            Rounded amount
        """
        if decimal_places == 0:
            return amount.quantize(Decimal('1'))
        else:
            quantizer = Decimal('0.1') ** decimal_places
            return amount.quantize(quantizer)

    def calculate_for_multiple_new_lps(
        self,
        new_lps: List[Partner],
        capital_calls: List[CapitalCall]
    ) -> List[NewLPCalculation]:
        """
        Calculate late interest for multiple new LPs.

        Args:
            new_lps: List of new LPs joining the fund
            capital_calls: All capital calls

        Returns:
            List of calculations for each new LP
        """
        return [
            self.calculate_late_interest_for_new_lp(lp, capital_calls)
            for lp in new_lps
        ]
