"""
Test script for pro-rata allocation calculator.
Tests standard allocation and edge case for LP commitment increases.
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
    EndDateCalculation,
    NewLPCalculation,
    LateInterestDetail
)
from app.calculators.late_interest_calculator import LateInterestCalculator
from app.calculators.allocation_calculator import AllocationCalculator


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def test_basic_allocation():
    """Test basic pro-rata allocation without commitment increases"""
    print_section("TEST 1: BASIC PRO-RATA ALLOCATION")

    # Set up fund assumptions
    assumptions = FundAssumptions(
        fund_name="Test Fund",
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

    # Close 1: Three existing LPs
    existing_lps = [
        Partner(name="Partner A", commitment=Decimal('1000000'), issue_date=date(2022, 4, 1), close_number=1),
        Partner(name="Partner B", commitment=Decimal('2000000'), issue_date=date(2022, 4, 1), close_number=1),
        Partner(name="Partner C", commitment=Decimal('500000'), issue_date=date(2022, 4, 1), close_number=1),
    ]

    # Close 2: One new LP joins
    new_lp = Partner(
        name="Partner D",
        commitment=Decimal('1500000'),
        issue_date=date(2023, 6, 1),
        close_number=2
    )

    # Capital calls that Partner D missed
    capital_calls = [
        CapitalCall(call_number=1, due_date=date(2022, 5, 1), call_percentage=Decimal('25.0')),
        CapitalCall(call_number=2, due_date=date(2022, 12, 1), call_percentage=Decimal('15.0')),
    ]

    # Calculate late interest owed by new LP
    late_calc = LateInterestCalculator(assumptions)
    new_lp_calc = late_calc.calculate_late_interest_for_new_lp(new_lp, capital_calls)

    print(f"\nNew LP: {new_lp.name}")
    print(f"Commitment: ${new_lp.commitment:,.2f}")
    print(f"Total Late Interest Due: ${new_lp_calc.total_late_interest_due:,.2f}")

    # Calculate allocations
    all_partners = existing_lps + [new_lp]
    alloc_calc = AllocationCalculator(assumptions)
    allocations, total_allocated = alloc_calc.calculate_allocations(
        new_lps=[new_lp_calc],
        all_partners=all_partners,
        admitting_close_number=2
    )

    # Display results
    print("\n" + "-" * 80)
    print("PRO-RATA ALLOCATION TO EXISTING LPs")
    print("-" * 80)

    total_existing_commitment = sum(lp.commitment for lp in existing_lps)
    print(f"{'Partner':<15} {'Commitment':<20} {'% Ownership':<15} {'Allocation':<20}")
    print("-" * 80)

    for alloc in allocations:
        pct = (alloc.commitment / total_existing_commitment) * Decimal('100')
        print(f"{alloc.partner_name:<15} ${alloc.commitment:>18,.2f} "
              f"{pct:>13.2f}% ${alloc.total_allocation:>18,.2f}")

    print("-" * 80)
    print(f"{'TOTAL':<15} ${total_existing_commitment:>18,.2f} "
          f"{'100.00%':>14} ${total_allocated:>18,.2f}")

    # Verify totals match
    print(f"\n{'Late Interest Collected:':<30} ${new_lp_calc.total_late_interest_due:,.2f}")
    print(f"{'Late Interest Allocated:':<30} ${total_allocated:,.2f}")
    diff = new_lp_calc.total_late_interest_due - total_allocated
    print(f"{'Difference:':<30} ${diff:,.2f}")

    if abs(diff) < Decimal('0.01'):
        print("\n✓ Allocation balances with collection (within rounding)")
    else:
        print(f"\n⚠ Warning: Allocation differs by ${diff:,.2f}")


def test_commitment_increase_allocation():
    """Test allocation when an existing LP increases their commitment"""
    print_section("TEST 2: ALLOCATION WITH COMMITMENT INCREASE (EDGE CASE)")

    # Set up fund assumptions
    assumptions = FundAssumptions(
        fund_name="Test Fund",
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

    # Close 1: Two existing LPs
    existing_lps = [
        Partner(name="Partner A", commitment=Decimal('1000000'), issue_date=date(2022, 4, 1), close_number=1),
        Partner(name="Partner B", commitment=Decimal('2000000'), issue_date=date(2022, 4, 1), close_number=1),
    ]

    # Close 2: Partner A increases commitment + one truly new LP joins
    # Partner A increases from $1M to $2M (increase of $1M)
    partner_a_increased = Partner(
        name="Partner A",
        commitment=Decimal('2000000'),  # New total commitment
        issue_date=date(2023, 6, 1),
        close_number=2  # Participating in Close 2
    )

    new_lp = Partner(
        name="Partner C",
        commitment=Decimal('500000'),
        issue_date=date(2023, 6, 1),
        close_number=2
    )

    # Capital calls before Close 2
    capital_calls = [
        CapitalCall(call_number=1, due_date=date(2022, 5, 1), call_percentage=Decimal('25.0')),
        CapitalCall(call_number=2, due_date=date(2022, 12, 1), call_percentage=Decimal('15.0')),
    ]

    # Calculate late interest
    late_calc = LateInterestCalculator(assumptions)

    # Partner A owes late interest on their $1M INCREASE
    partner_a_increase_amount = Decimal('1000000')  # The increase amount
    partner_a_increase_calc = late_calc.calculate_late_interest_for_new_lp(
        Partner(
            name="Partner A (Increase)",
            commitment=partner_a_increase_amount,
            issue_date=date(2023, 6, 1),
            close_number=2
        ),
        capital_calls
    )

    # Partner C owes late interest on full commitment
    new_lp_calc = late_calc.calculate_late_interest_for_new_lp(new_lp, capital_calls)

    print("\nLate Interest Due:")
    print(f"  Partner A (increase of ${partner_a_increase_amount:,.2f}): "
          f"${partner_a_increase_calc.total_late_interest_due:,.2f}")
    print(f"  Partner C (new LP): ${new_lp_calc.total_late_interest_due:,.2f}")

    total_late_interest = (partner_a_increase_calc.total_late_interest_due +
                          new_lp_calc.total_late_interest_due)
    print(f"  Total Late Interest Collected: ${total_late_interest:,.2f}")

    # For allocation: Partner A gets allocated based on ORIGINAL $1M commitment
    # Partner B gets allocated based on their $2M commitment
    commitment_increases = {
        "Partner A": Decimal('1000000')  # Partner A's ORIGINAL commitment
    }

    # Update all_partners to reflect Close 2 state
    all_partners = [
        existing_lps[0],  # Partner A at Close 1 (original commitment)
        existing_lps[1],  # Partner B at Close 1
        partner_a_increased,  # Partner A updated for Close 2
        new_lp  # Partner C joining at Close 2
    ]

    # Calculate allocations with increase handling
    alloc_calc = AllocationCalculator(assumptions)
    allocations, total_allocated = alloc_calc.calculate_allocations_with_increases(
        new_lps=[partner_a_increase_calc, new_lp_calc],
        all_partners=all_partners,
        commitment_increases=commitment_increases,
        admitting_close_number=2
    )

    # Display results
    print("\n" + "-" * 80)
    print("PRO-RATA ALLOCATION TO EXISTING LPs")
    print("-" * 80)

    # Calculate allocation base (original commitments)
    total_allocation_base = Decimal('1000000') + Decimal('2000000')  # Partner A original + Partner B

    print(f"{'Partner':<15} {'Current Commit':<20} {'Alloc. Base':<20} "
          f"{'% Share':<12} {'Allocation':<20}")
    print("-" * 80)

    alloc_bases = {
        "Partner A": Decimal('1000000'),  # Original commitment
        "Partner B": Decimal('2000000'),
    }

    for alloc in allocations:
        alloc_base = alloc_bases.get(alloc.partner_name, Decimal('0'))
        if alloc_base > 0:
            pct = (alloc_base / total_allocation_base) * Decimal('100')
            print(f"{alloc.partner_name:<15} ${alloc.commitment:>18,.2f} "
                  f"${alloc_base:>18,.2f} {pct:>10.2f}% "
                  f"${alloc.total_allocation:>18,.2f}")

    print("-" * 80)
    print(f"{'TOTAL':<56} {'100.00%':>11} ${total_allocated:>18,.2f}")

    # Verify
    print(f"\n{'Late Interest Collected:':<30} ${total_late_interest:,.2f}")
    print(f"{'Late Interest Allocated:':<30} ${total_allocated:,.2f}")
    diff = total_late_interest - total_allocated
    print(f"{'Difference:':<30} ${diff:,.2f}")

    if abs(diff) < Decimal('0.01'):
        print("\n✓ Allocation balances with collection (within rounding)")
    else:
        print(f"\n⚠ Warning: Allocation differs by ${diff:,.2f}")

    # Explain the edge case
    print("\n" + "-" * 80)
    print("EDGE CASE EXPLANATION:")
    print("-" * 80)
    print("Partner A:")
    print(f"  • Original commitment (Close 1): $1,000,000")
    print(f"  • New commitment (Close 2): $2,000,000")
    print(f"  • Increase: $1,000,000")
    print(f"  • Pays late interest on: ${partner_a_increase_amount:,.2f} (the increase)")
    print(f"  • Receives allocation on: $1,000,000 (original commitment)")
    print(f"  • Allocation received: ${allocations[0].total_allocation:,.2f}")
    print(f"\n  Partner A effectively allocates ${allocations[0].total_allocation:,.2f}")
    print(f"  to themselves from the ${partner_a_increase_calc.total_late_interest_due:,.2f}")
    print(f"  they paid in late interest.")


def test_multiple_closes():
    """Test allocation across multiple closes"""
    print_section("TEST 3: ALLOCATION ACROSS MULTIPLE CLOSES")

    assumptions = FundAssumptions(
        fund_name="Test Fund",
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

    # Close 1: Two LPs
    close_1_lps = [
        Partner(name="Partner A", commitment=Decimal('1000000'), issue_date=date(2022, 4, 1), close_number=1),
        Partner(name="Partner B", commitment=Decimal('1000000'), issue_date=date(2022, 4, 1), close_number=1),
    ]

    # Close 2: One new LP
    close_2_lp = Partner(name="Partner C", commitment=Decimal('500000'), issue_date=date(2023, 6, 1), close_number=2)

    # Close 3: One new LP
    close_3_lp = Partner(name="Partner D", commitment=Decimal('500000'), issue_date=date(2024, 6, 1), close_number=3)

    # Capital calls
    capital_calls = [
        CapitalCall(call_number=1, due_date=date(2022, 5, 1), call_percentage=Decimal('20.0')),
        CapitalCall(call_number=2, due_date=date(2023, 1, 1), call_percentage=Decimal('15.0')),
        CapitalCall(call_number=3, due_date=date(2023, 8, 1), call_percentage=Decimal('10.0')),
    ]

    late_calc = LateInterestCalculator(assumptions)
    alloc_calc = AllocationCalculator(assumptions)

    # Calculate late interest for Close 2
    close_2_calc = late_calc.calculate_late_interest_for_new_lp(close_2_lp, capital_calls)

    # Calculate late interest for Close 3
    close_3_calc = late_calc.calculate_late_interest_for_new_lp(close_3_lp, capital_calls)

    print(f"\nClose 2: Partner C joins")
    print(f"  Late Interest Due: ${close_2_calc.total_late_interest_due:,.2f}")

    print(f"\nClose 3: Partner D joins")
    print(f"  Late Interest Due: ${close_3_calc.total_late_interest_due:,.2f}")

    # Allocate Close 2
    all_partners_c2 = close_1_lps + [close_2_lp]
    alloc_c2, total_c2 = alloc_calc.calculate_allocations(
        new_lps=[close_2_calc],
        all_partners=all_partners_c2,
        admitting_close_number=2
    )

    # Allocate Close 3
    all_partners_c3 = close_1_lps + [close_2_lp, close_3_lp]
    alloc_c3, total_c3 = alloc_calc.calculate_allocations(
        new_lps=[close_3_calc],
        all_partners=all_partners_c3,
        admitting_close_number=3
    )

    # Aggregate
    allocations_by_close = {2: alloc_c2, 3: alloc_c3}
    aggregated = alloc_calc.aggregate_allocations_across_closes(allocations_by_close)

    # Display
    print("\n" + "-" * 80)
    print("ALLOCATION BY CLOSE")
    print("-" * 80)
    print(f"{'Partner':<15} {'Close 2':<20} {'Close 3':<20} {'Total':<20}")
    print("-" * 80)

    for alloc in aggregated:
        c2_amt = alloc.allocation_by_admitting_close.get(2, Decimal('0'))
        c3_amt = alloc.allocation_by_admitting_close.get(3, Decimal('0'))
        print(f"{alloc.partner_name:<15} ${c2_amt:>18,.2f} "
              f"${c3_amt:>18,.2f} ${alloc.total_allocation:>18,.2f}")

    print("-" * 80)
    print(f"{'TOTAL':<15} ${total_c2:>18,.2f} ${total_c3:>18,.2f} "
          f"${total_c2 + total_c3:>18,.2f}")


if __name__ == "__main__":
    test_basic_allocation()
    test_commitment_increase_allocation()
    test_multiple_closes()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
