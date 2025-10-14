#!/usr/bin/env python3
"""
Test script for late_interest_engine programmatic usage
This demonstrates using the engine without CSV or interactive mode
"""

import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from late_interest_engine import LateInterestEngine, parse_natural_currency, parse_flexible_date
from app.models.data_models import (
    Partner,
    CapitalCall,
    FundAssumptions,
    PrimeRateChange,
    InterestBase,
    InterestCompounding,
    EndDateCalculation
)

def main():
    print("Testing Late Interest Engine - Programmatic Mode")
    print("=" * 80)

    # Test natural language parsing
    print("\n1. Testing Natural Language Parsers:")
    print("-" * 80)

    test_amounts = ["10m", "5M", "2.5m", "500k", "$1,000,000"]
    for amount in test_amounts:
        parsed = parse_natural_currency(amount)
        print(f"  '{amount}' -> ${parsed:,.0f}")

    test_dates = ["1/15/22", "Jan 15 2023", "2023-01-15"]
    print()
    for date_str in test_dates:
        parsed = parse_flexible_date(date_str)
        print(f"  '{date_str}' -> {parsed}")

    # Set up example scenario
    print("\n\n2. Running Example Calculation:")
    print("-" * 80)
    print("Scenario: 10M in commitments, 3 capital calls, 1 subsequent close LP")

    # Create capital calls
    capital_calls = [
        CapitalCall(call_number=1, due_date=date(2022, 1, 15), call_percentage=Decimal('10')),
        CapitalCall(call_number=2, due_date=date(2022, 6, 15), call_percentage=Decimal('15')),
        CapitalCall(call_number=3, due_date=date(2022, 12, 15), call_percentage=Decimal('20')),
    ]

    # Create partners
    partners = [
        # Existing LPs (Close 1)
        Partner(name="ABC Partners", issue_date=date(2022, 1, 15),
                commitment=Decimal('5000000'), close_number=1),
        Partner(name="XYZ Capital", issue_date=date(2022, 1, 15),
                commitment=Decimal('5000000'), close_number=1),

        # New LP (Close 2) - joined after first 2 capital calls
        Partner(name="New Investor LLC", issue_date=date(2022, 7, 1),
                commitment=Decimal('3000000'), close_number=2),
    ]

    print(f"\nCapital Calls:")
    for call in capital_calls:
        print(f"  Call #{call.call_number}: {call.due_date}, {call.call_percentage}%")

    print(f"\nPartners:")
    for partner in partners:
        print(f"  {partner.name}: ${partner.commitment:,.0f} (Close {partner.close_number})")

    # Set up fund assumptions
    assumptions = FundAssumptions(
        fund_name="Test Fund IV",
        late_interest_base=InterestBase.PRIME,
        late_spread=Decimal('2.0'),
        prime_rate_history=[
            PrimeRateChange(effective_date=date(2020, 1, 1), rate=Decimal('7.5'))
        ],
        late_interest_compounding=InterestCompounding.SIMPLE,
        end_date_calculation=EndDateCalculation.ISSUE_DATE,
        mgmt_fee_allocated_interest=False,
        allocated_to_all_existing_lps=True,
        calc_rounding=2,
        sum_rounding=2
    )

    print(f"\nSettings:")
    print(f"  Prime Rate: 7.5%")
    print(f"  Spread: 2.0%")
    print(f"  Total Rate: 9.5%")
    print(f"  Compounding: Simple")

    # Run calculation
    print("\n" + "=" * 80)
    print("RUNNING CALCULATION")
    print("=" * 80)

    engine = LateInterestEngine(assumptions)
    output = engine.run_complete_calculation(
        partners=partners,
        capital_calls=capital_calls,
        verbose=True
    )

    print("\n\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\nTotal Late Interest Collected: ${output.total_late_interest_collected}")
    print(f"Total Late Interest Allocated: ${output.total_late_interest_allocated}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
