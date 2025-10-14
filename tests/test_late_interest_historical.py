"""
Test script to verify late interest calculations match historical data.
Tests the "New LP" example from the ex late interest tab.csv

Expected Results (from CSV):
- Prime Rate: 7.25% + 2% spread = 9.25% total
- Total Catch-Up: $3,500,000
- Total Late Interest Due: $704,223.29

Capital Calls:
1. Cap Call 1 (4/20/22): $1,000,000 → $336,013.70 late interest
2. Cap Call 2 (1/23/23): $500,000 → $131,828.77 late interest
3. Cap Call 3 (7/11/23): $150,000 → $32,950.68 late interest
4. Cap Call 4 (3/15/24): $850,000 → $131,854.79 late interest
5. Cap Call 5 (9/26/24): $250,000 → $26,092.47 late interest
6. Cap Call 6 (3/13/25): $750,000 → $45,482.88 late interest
"""

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.models.data_models import (
    Partner,
    CapitalCall,
    FundAssumptions,
    PrimeRateChange,
    InterestBase,
    InterestCompounding,
    EndDateCalculation
)
from app.calculators.late_interest_calculator import LateInterestCalculator


def test_historical_match():
    """Test that calculations match the historical CSV data"""

    # Set up fund assumptions to match historical data
    # Historical data uses 9.5% total rate (reverse-engineered from actual calculations)
    # This equals Prime 7.5% + 2% spread = 9.5%
    assumptions = FundAssumptions(
        fund_name="Test Fund",
        late_interest_base=InterestBase.PRIME,
        late_spread=Decimal('2.0'),  # 2% spread
        prime_rate_history=[
            PrimeRateChange(effective_date=date(2020, 1, 1), rate=Decimal('7.5'))
        ],
        late_interest_compounding=InterestCompounding.SIMPLE,
        end_date_calculation=EndDateCalculation.ISSUE_DATE,
        mgmt_fee_allocated_interest=False,
        allocated_to_all_existing_lps=False,
        calc_rounding=2,
        sum_rounding=2
    )

    # Create the New LP
    new_lp = Partner(
        name="New LP",
        commitment=Decimal('5000000.00'),
        issue_date=date(2025, 10, 31),
        close_number=2
    )

    # Create capital calls from historical data
    capital_calls = [
        CapitalCall(
            call_number=1,
            due_date=date(2022, 4, 20),
            call_percentage=Decimal('20.0')
        ),
        CapitalCall(
            call_number=2,
            due_date=date(2023, 1, 23),
            call_percentage=Decimal('10.0')
        ),
        CapitalCall(
            call_number=3,
            due_date=date(2023, 7, 11),
            call_percentage=Decimal('3.0')
        ),
        CapitalCall(
            call_number=4,
            due_date=date(2024, 3, 15),
            call_percentage=Decimal('17.0')
        ),
        CapitalCall(
            call_number=5,
            due_date=date(2024, 9, 26),
            call_percentage=Decimal('5.0')
        ),
        CapitalCall(
            call_number=6,
            due_date=date(2025, 3, 13),
            call_percentage=Decimal('15.0')
        ),
    ]

    # Expected results from CSV
    expected_results = {
        1: {'capital': Decimal('1000000.00'), 'interest': Decimal('336013.70')},
        2: {'capital': Decimal('500000.00'), 'interest': Decimal('131828.77')},
        3: {'capital': Decimal('150000.00'), 'interest': Decimal('32950.68')},
        4: {'capital': Decimal('850000.00'), 'interest': Decimal('131854.79')},
        5: {'capital': Decimal('250000.00'), 'interest': Decimal('26092.47')},
        6: {'capital': Decimal('750000.00'), 'interest': Decimal('45482.88')},
    }
    expected_total_interest = Decimal('704223.29')
    expected_total_catchup = Decimal('3500000.00')

    # Calculate using our Python code
    calculator = LateInterestCalculator(assumptions)
    result = calculator.calculate_late_interest_for_new_lp(new_lp, capital_calls)

    # Print results
    print("=" * 80)
    print("LATE INTEREST CALCULATION TEST - HISTORICAL DATA VALIDATION")
    print("=" * 80)
    print(f"\nPartner: {result.partner_name}")
    print(f"Commitment: ${result.commitment:,.2f}")
    print(f"Issue Date: {result.issue_date}")
    print(f"Rate Used: Prime 7.5% + 2% spread = 9.5%")
    print("\n" + "-" * 80)
    print(f"{'Call':<6} {'Due Date':<12} {'Capital':<20} {'Late Interest':<20} {'Match':<10}")
    print("-" * 80)

    all_match = True
    for detail in result.breakdown_by_capital_call:
        call_num = detail.call_number
        expected = expected_results[call_num]

        capital_match = detail.capital_amount == expected['capital']
        interest_match = detail.late_interest == expected['interest']
        match = capital_match and interest_match

        match_str = "✓ MATCH" if match else "✗ MISMATCH"
        if not match:
            all_match = False

        print(f"{call_num:<6} {detail.due_date!s:<12} "
              f"${detail.capital_amount:>18,.2f} "
              f"${detail.late_interest:>18,.2f} "
              f"{match_str:<10}")

        if not capital_match:
            print(f"       {'':12} Expected capital: ${expected['capital']:>18,.2f}")
        if not interest_match:
            print(f"       {'':12} Expected interest: ${expected['interest']:>18,.2f}")
            diff = detail.late_interest - expected['interest']
            print(f"       {'':12} Difference: ${diff:>18,.2f}")

    print("-" * 80)
    print(f"{'TOTAL':<18} ${result.total_catch_up:>18,.2f} ${result.total_late_interest_due:>18,.2f}")
    print(f"{'EXPECTED':<18} ${expected_total_catchup:>18,.2f} ${expected_total_interest:>18,.2f}")

    catchup_match = result.total_catch_up == expected_total_catchup
    interest_match = result.total_late_interest_due == expected_total_interest

    print("\n" + "=" * 80)
    print("VALIDATION RESULTS:")
    print("=" * 80)
    print(f"Total Catch-Up Match: {'✓ YES' if catchup_match else '✗ NO'}")
    if not catchup_match:
        diff = result.total_catch_up - expected_total_catchup
        print(f"  Difference: ${diff:,.2f}")

    print(f"Total Late Interest Match: {'✓ YES' if interest_match else '✗ NO'}")
    if not interest_match:
        diff = result.total_late_interest_due - expected_total_interest
        print(f"  Difference: ${diff:,.2f}")
        pct_diff = (diff / expected_total_interest) * 100
        print(f"  Percentage Difference: {pct_diff:.4f}%")

    print(f"Individual Call Matches: {'✓ ALL MATCH' if all_match else '✗ SOME MISMATCHES'}")
    print("=" * 80)

    if all_match and catchup_match and interest_match:
        print("\n🎉 SUCCESS! All calculations match historical data perfectly!")
    else:
        print("\n⚠️  MISMATCH DETECTED - Review calculation methodology")

    return all_match and catchup_match and interest_match


if __name__ == "__main__":
    test_historical_match()
