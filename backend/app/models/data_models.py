"""
Data models for late interest calculation system.
Uses dataclasses for clean, typed data structures.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional
from enum import Enum


class InterestCompounding(Enum):
    """Late interest compounding method"""
    SIMPLE = "simple"
    COMPOUND = "compound"


class InterestBase(Enum):
    """Base rate for late interest calculation"""
    PRIME = "prime"
    FLAT = "flat"


class EndDateCalculation(Enum):
    """Method for calculating end date of late interest"""
    ISSUE_DATE = "issue_date"  # Calculate through LP admission date
    DUE_DATE = "due_date"  # Calculate only to capital call due date


@dataclass
class PrimeRateChange:
    """Historical prime rate change"""
    effective_date: date
    rate: Decimal  # As percentage, e.g., 7.25 for 7.25%


@dataclass
class FundAssumptions:
    """Configuration for late interest calculations"""
    fund_name: str
    late_interest_compounding: InterestCompounding
    late_interest_base: InterestBase
    late_spread: Decimal  # Percentage added to base rate (e.g., 2 for 2%)
    end_date_calculation: EndDateCalculation
    mgmt_fee_allocated_interest: bool
    allocated_to_all_existing_lps: bool
    calc_rounding: int  # Decimal places for intermediate calculations
    sum_rounding: int  # Decimal places for final sums
    prime_rate_history: List[PrimeRateChange] = field(default_factory=list)
    flat_rate: Optional[Decimal] = None  # Used if late_interest_base is FLAT


@dataclass
class Partner:
    """LP/Partner in the fund"""
    name: str
    issue_date: date
    commitment: Decimal
    close_number: int


@dataclass
class CapitalCall:
    """Capital call details"""
    call_number: int
    due_date: date
    call_percentage: Decimal  # As percentage, e.g., 20 for 20%

    def get_call_amount(self, commitment: Decimal) -> Decimal:
        """Calculate the capital call amount for a given commitment"""
        return commitment * (self.call_percentage / Decimal('100'))


@dataclass
class LateInterestDetail:
    """Late interest calculation for a single capital call"""
    call_number: int
    due_date: date
    call_percentage: Decimal
    capital_amount: Decimal
    late_interest: Decimal
    days_late: int
    effective_rate: Decimal  # The actual rate used (may be weighted average)


@dataclass
class NewLPCalculation:
    """Complete late interest calculation for a new LP"""
    partner_name: str
    issue_date: date
    commitment: Decimal
    close_number: int
    total_catch_up: Decimal
    total_late_interest_due: Decimal
    breakdown_by_capital_call: List[LateInterestDetail]


@dataclass
class ExistingLPAllocation:
    """Late interest allocation to an existing LP"""
    partner_name: str
    commitment: Decimal
    close_number: int
    total_allocation: Decimal
    allocation_by_admitting_close: dict  # Maps admitting close number to allocation amount


@dataclass
class LateInterestCalculationResult:
    """Complete result of late interest calculation"""
    fund_name: str
    calculation_date: date
    new_lps: List[NewLPCalculation]
    existing_lps: List[ExistingLPAllocation]
    total_late_interest_collected: Decimal
    total_late_interest_allocated: Decimal
