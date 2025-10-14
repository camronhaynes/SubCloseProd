"""
LATE INTEREST ENGINE - Complete Calculator
===========================================

This script provides a complete late interest calculation system for private equity funds
with subsequent closes. It handles:
- Late interest calculations for new LPs joining at subsequent closes
- Pro-rata allocation to existing LPs
- Edge cases like commitment increases
- Multiple closes and aggregation
- Flexible input from CSV or programmatic data

Usage:
    python3 late_interest_engine.py --csv <path_to_csv> [options]
    python3 late_interest_engine.py --interactive [options]

    Or import and use programmatically:
    from late_interest_engine import LateInterestEngine
"""

import sys
import csv
import argparse
import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import json

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
from app.calculators.allocation_calculator import AllocationCalculator


# ============================================================================
# DATA MODELS FOR OUTPUT
# ============================================================================

@dataclass
class EngineOutput:
    """Complete output from the late interest engine"""
    fund_name: str
    calculation_date: str
    total_late_interest_collected: str
    total_late_interest_allocated: str
    new_lps: List[Dict]
    existing_lps: List[Dict]
    summary_by_close: List[Dict]
    settings: Dict


# ============================================================================
# PARSING UTILITIES
# ============================================================================

def parse_date(date_str: str) -> Optional[date]:
    """Parse date from various formats"""
    if not date_str or date_str.strip() == '':
        return None

    formats = ['%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_currency(value: str) -> Decimal:
    """Parse currency string to Decimal"""
    if not value or value.strip() in ['', '-', '$-', '$   -']:
        return Decimal('0')

    cleaned = value.replace('$', '').replace(',', '').replace(' ', '').strip()
    if cleaned == '' or cleaned == '-':
        return Decimal('0')

    return Decimal(cleaned)


def parse_percentage(value: str) -> Decimal:
    """Parse percentage string to Decimal"""
    if not value or value.strip() in ['', '-']:
        return Decimal('0')

    cleaned = value.replace('%', '').strip()
    if cleaned == '' or cleaned == '-':
        return Decimal('0')

    return Decimal(cleaned)


def parse_natural_currency(value: str) -> Decimal:
    """
    Parse natural language currency input to Decimal.

    Examples:
        "10m" -> 10,000,000
        "5M" -> 5,000,000
        "2.5m" -> 2,500,000
        "500k" -> 500,000
        "1.2k" -> 1,200
        "$10,000,000" -> 10,000,000
        "10000000" -> 10,000,000
    """
    if not value or value.strip() in ['', '-']:
        return Decimal('0')

    # Clean the input
    cleaned = value.lower().replace('$', '').replace(',', '').replace(' ', '').strip()

    if cleaned == '' or cleaned == '-':
        return Decimal('0')

    # Check for suffixes
    multiplier = Decimal('1')
    if cleaned.endswith('m'):
        multiplier = Decimal('1000000')
        cleaned = cleaned[:-1]
    elif cleaned.endswith('k'):
        multiplier = Decimal('1000')
        cleaned = cleaned[:-1]
    elif cleaned.endswith('b'):
        multiplier = Decimal('1000000000')
        cleaned = cleaned[:-1]

    try:
        return Decimal(cleaned) * multiplier
    except:
        raise ValueError(f"Could not parse currency value: {value}")


def parse_flexible_date(date_str: str) -> date:
    """
    Parse date from various formats including natural language.

    Examples:
        "1/15/23" -> January 15, 2023
        "01/15/2023" -> January 15, 2023
        "2023-01-15" -> January 15, 2023
        "Jan 15 2023" -> January 15, 2023
        "January 15, 2023" -> January 15, 2023
    """
    if not date_str or date_str.strip() == '':
        raise ValueError("Date string is empty")

    date_str = date_str.strip()

    # Try standard formats first
    formats = [
        '%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%Y/%m/%d',
        '%b %d %Y', '%B %d %Y', '%b %d, %Y', '%B %d, %Y',
        '%d %b %Y', '%d %B %Y', '%d %b, %Y', '%d %B, %Y'
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Could not parse date: {date_str}")


# ============================================================================
# CSV LOADING
# ============================================================================

def load_from_csv(csv_path: str) -> Tuple[List[Partner], List[CapitalCall]]:
    """
    Load partners and capital calls from the 'ex late interest tab.csv' format.
    """
    partners = []
    capital_calls = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        lines = list(csv.reader(f))

    # Parse capital calls from header rows
    if len(lines) > 2:
        header_row = lines[0]
        due_date_row = lines[1]
        call_pct_row = lines[2]

        i = 0
        while i < len(header_row):
            cell = header_row[i]
            if cell and 'Cap Call' in cell:
                if i + 1 < len(header_row):
                    try:
                        call_num_str = header_row[i + 1].strip()
                        if call_num_str.isdigit():
                            call_num = int(call_num_str)

                            due_date_str = due_date_row[i + 1] if i + 1 < len(due_date_row) else ''
                            call_pct_str = call_pct_row[i + 1] if i + 1 < len(call_pct_row) else ''

                            if due_date_str and call_pct_str:
                                due_date = parse_date(due_date_str)
                                call_pct = parse_percentage(call_pct_str)

                                if due_date and call_pct > 0:
                                    capital_calls.append(CapitalCall(
                                        call_number=call_num,
                                        due_date=due_date,
                                        call_percentage=call_pct
                                    ))
                    except:
                        pass
            i += 1

    # Parse new LP from row 4 if present
    if len(lines) > 4:
        new_lp_row = lines[4]
        if len(new_lp_row) > 4:
            try:
                partner_name = new_lp_row[1].strip() if new_lp_row[1] else ''
                issue_date_str = new_lp_row[2] if len(new_lp_row) > 2 else ''
                commitment_str = new_lp_row[3] if len(new_lp_row) > 3 else ''
                close_str = new_lp_row[4] if len(new_lp_row) > 4 else ''

                if partner_name and partner_name not in ['', 'Partner']:
                    issue_date = parse_date(issue_date_str)
                    commitment = parse_currency(commitment_str)
                    close_num = int(close_str.strip()) if close_str and close_str.strip().isdigit() else 2

                    if commitment > 0 and issue_date:
                        partners.append(Partner(
                            name=partner_name,
                            issue_date=issue_date,
                            commitment=commitment,
                            close_number=close_num
                        ))
            except:
                pass

    # Parse existing partners starting from row 18
    for i in range(18, len(lines)):
        row = lines[i]
        if len(row) < 4:
            continue

        partner_name = row[1].strip() if len(row) > 1 else ''
        if not partner_name or partner_name in ['Partner', '']:
            continue

        try:
            issue_date_str = row[2] if len(row) > 2 else ''
            commitment_str = row[3] if len(row) > 3 else ''
            close_str = row[4] if len(row) > 4 else ''

            issue_date = parse_date(issue_date_str)
            commitment = parse_currency(commitment_str)
            close_num = int(close_str.strip()) if close_str and close_str.strip().isdigit() else 1

            if commitment > 0:
                partners.append(Partner(
                    name=partner_name,
                    issue_date=issue_date if issue_date else date(2022, 4, 1),
                    commitment=commitment,
                    close_number=close_num
                ))
        except:
            continue

    return partners, capital_calls


# ============================================================================
# INTERACTIVE INPUT MODE
# ============================================================================

def interactive_input_mode() -> Tuple[List[Partner], List[CapitalCall]]:
    """
    Interactive mode to collect fund data from user input.
    Returns partners and capital calls.
    """
    print("\n" + "=" * 80)
    print("LATE INTEREST ENGINE - INTERACTIVE INPUT MODE".center(80))
    print("=" * 80)
    print("\nEnter fund data interactively. You can use natural language for amounts:")
    print("  Examples: '10m', '5M', '2.5m', '500k', '$10,000,000'")
    print("  Dates: '1/15/23', 'Jan 15 2023', '2023-01-15'\n")

    partners = []
    capital_calls = []

    # ========== CAPITAL CALLS ==========
    print("\n" + "-" * 80)
    print("CAPITAL CALLS")
    print("-" * 80)
    print("Enter capital call information. Type 'done' when finished.\n")

    call_num = 1
    while True:
        print(f"\nCapital Call #{call_num}:")

        # Due date
        due_date_str = input(f"  Due date (e.g., '1/15/23' or 'done'): ").strip()
        if due_date_str.lower() == 'done':
            break

        try:
            due_date = parse_flexible_date(due_date_str)
        except ValueError as e:
            print(f"  ⚠ Error: {e}. Please try again.")
            continue

        # Call percentage
        pct_str = input(f"  Call percentage (e.g., '10' for 10%): ").strip()
        try:
            call_pct = parse_percentage(pct_str)
            if call_pct <= 0:
                print("  ⚠ Error: Percentage must be greater than 0. Please try again.")
                continue
        except Exception as e:
            print(f"  ⚠ Error: {e}. Please try again.")
            continue

        capital_calls.append(CapitalCall(
            call_number=call_num,
            due_date=due_date,
            call_percentage=call_pct
        ))

        print(f"  ✓ Added Capital Call #{call_num}: {due_date}, {call_pct}%")
        call_num += 1

    if not capital_calls:
        print("\n⚠ Warning: No capital calls entered. You must have at least one capital call.")
        return partners, capital_calls

    print(f"\n✓ Total capital calls entered: {len(capital_calls)}")

    # ========== PARTNERS / LPs ==========
    print("\n" + "-" * 80)
    print("PARTNERS / LIMITED PARTNERS")
    print("-" * 80)
    print("Enter partner information. Type 'done' when finished.\n")

    partner_num = 1
    while True:
        print(f"\nPartner #{partner_num}:")

        # Partner name
        name = input(f"  Partner name (or 'done'): ").strip()
        if name.lower() == 'done':
            break

        if not name:
            print("  ⚠ Error: Partner name cannot be empty.")
            continue

        # Commitment
        commitment_str = input(f"  Commitment (e.g., '10m', '5M', '500k'): ").strip()
        try:
            commitment = parse_natural_currency(commitment_str)
            if commitment <= 0:
                print("  ⚠ Error: Commitment must be greater than 0. Please try again.")
                continue
        except Exception as e:
            print(f"  ⚠ Error: {e}. Please try again.")
            continue

        # Issue date (optional)
        issue_date_str = input(f"  Issue date (press Enter for first capital call date): ").strip()
        if issue_date_str:
            try:
                issue_date = parse_flexible_date(issue_date_str)
            except ValueError as e:
                print(f"  ⚠ Error: {e}. Please try again.")
                continue
        else:
            # Default to first capital call date
            issue_date = capital_calls[0].due_date if capital_calls else date.today()

        # Close number
        close_str = input(f"  Close number (1 for initial, 2+ for subsequent, default=1): ").strip()
        if close_str:
            try:
                close_num = int(close_str)
                if close_num < 1:
                    print("  ⚠ Error: Close number must be at least 1. Please try again.")
                    continue
            except ValueError:
                print("  ⚠ Error: Close number must be an integer. Please try again.")
                continue
        else:
            close_num = 1

        partners.append(Partner(
            name=name,
            issue_date=issue_date,
            commitment=commitment,
            close_number=close_num
        ))

        print(f"  ✓ Added Partner: {name}, ${commitment:,.0f}, Close {close_num}")
        partner_num += 1

    if not partners:
        print("\n⚠ Warning: No partners entered. You must have at least one partner.")
        return partners, capital_calls

    print(f"\n✓ Total partners entered: {len(partners)}")

    # Summary
    print("\n" + "=" * 80)
    print("INPUT SUMMARY")
    print("=" * 80)
    print(f"Capital Calls: {len(capital_calls)}")
    for call in capital_calls:
        print(f"  Call #{call.call_number}: {call.due_date}, {call.call_percentage}%")

    print(f"\nPartners: {len(partners)}")
    for partner in partners:
        print(f"  {partner.name}: ${partner.commitment:,.0f}, Close {partner.close_number}")

    print("\n" + "=" * 80)

    # Confirm
    confirm = input("\nProceed with calculation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return [], []

    return partners, capital_calls


# ============================================================================
# MAIN ENGINE CLASS
# ============================================================================

class LateInterestEngine:
    """
    Complete late interest calculation engine.

    This class orchestrates late interest calculations and allocations
    for any fund structure with subsequent closes.
    """

    def __init__(self, assumptions: FundAssumptions):
        """
        Initialize the engine with fund assumptions.

        Args:
            assumptions: Fund-level calculation settings
        """
        self.assumptions = assumptions
        self.late_calc = LateInterestCalculator(assumptions)
        self.alloc_calc = AllocationCalculator(assumptions)

    def run_complete_calculation(
        self,
        partners: List[Partner],
        capital_calls: List[CapitalCall],
        commitment_increases: Optional[Dict[str, Decimal]] = None,
        verbose: bool = True
    ) -> EngineOutput:
        """
        Run complete late interest calculation for all closes.

        Args:
            partners: All partners in the fund
            capital_calls: All capital calls
            commitment_increases: Optional dict of partner_name -> original_commitment
                                 for partners who increased their commitment
            verbose: Print detailed output to console

        Returns:
            EngineOutput with complete calculation results
        """
        if verbose:
            self._print_header("LATE INTEREST ENGINE - COMPLETE CALCULATION")

        # Sort and group partners by close
        partners.sort(key=lambda p: p.close_number)
        partners_by_close: Dict[int, List[Partner]] = {}
        for partner in partners:
            if partner.close_number not in partners_by_close:
                partners_by_close[partner.close_number] = []
            partners_by_close[partner.close_number].append(partner)

        all_closes = sorted(partners_by_close.keys())
        closes_to_process = all_closes[1:]  # Skip first close

        if verbose:
            self._print_summary(len(partners), len(capital_calls), all_closes)

        # Track results
        all_new_lp_results = []
        all_allocations_by_close = {}
        grand_total_collected = Decimal('0')
        grand_total_allocated = Decimal('0')
        close_summaries = []

        # Process each close
        for close_num in closes_to_process:
            if verbose:
                self._print_section_header(f"CLOSE {close_num}")

            # Identify new LPs and existing LPs
            new_lps_at_close = partners_by_close[close_num]
            existing_partners = [p for p in partners if p.close_number < close_num]

            # Calculate late interest for new LPs
            new_lp_calcs = []
            total_collected = Decimal('0')

            for new_lp in new_lps_at_close:
                calc = self.late_calc.calculate_late_interest_for_new_lp(new_lp, capital_calls)
                new_lp_calcs.append(calc)
                total_collected += calc.total_late_interest_due

                all_new_lp_results.append({
                    'partner_name': calc.partner_name,
                    'close_number': calc.close_number,
                    'commitment': str(calc.commitment),
                    'issue_date': str(calc.issue_date),
                    'total_catch_up': str(calc.total_catch_up),
                    'total_late_interest_due': str(calc.total_late_interest_due),
                    'breakdown': [
                        {
                            'call_number': d.call_number,
                            'due_date': str(d.due_date),
                            'call_percentage': str(d.call_percentage),
                            'capital_amount': str(d.capital_amount),
                            'late_interest': str(d.late_interest),
                            'days_late': d.days_late,
                            'effective_rate': str(d.effective_rate)
                        }
                        for d in calc.breakdown_by_capital_call
                    ]
                })

            grand_total_collected += total_collected

            if verbose:
                self._print_late_interest_table(new_lp_calcs, total_collected)

            # Calculate allocations
            allocations = []
            total_allocated = Decimal('0')

            if existing_partners and total_collected > 0:
                if commitment_increases:
                    allocations, total_allocated = self.alloc_calc.calculate_allocations_with_increases(
                        new_lps=new_lp_calcs,
                        all_partners=partners,
                        commitment_increases=commitment_increases,
                        admitting_close_number=close_num
                    )
                else:
                    allocations, total_allocated = self.alloc_calc.calculate_allocations(
                        new_lps=new_lp_calcs,
                        all_partners=partners,
                        admitting_close_number=close_num
                    )

                all_allocations_by_close[close_num] = allocations
                grand_total_allocated += total_allocated

                if verbose:
                    self._print_allocation_table(allocations, existing_partners, total_allocated)
                    self._print_balance_check(total_collected, total_allocated)

            # Close summary
            close_summaries.append({
                'close_number': close_num,
                'new_lps_count': len(new_lps_at_close),
                'existing_lps_count': len(existing_partners),
                'total_collected': str(total_collected),
                'total_allocated': str(total_allocated),
                'difference': str(total_collected - total_allocated)
            })

        # Aggregate allocations across closes
        aggregated_allocations = []
        if all_allocations_by_close:
            aggregated = self.alloc_calc.aggregate_allocations_across_closes(all_allocations_by_close)

            for alloc in aggregated:
                aggregated_allocations.append({
                    'partner_name': alloc.partner_name,
                    'commitment': str(alloc.commitment),
                    'close_number': alloc.close_number,
                    'total_allocation': str(alloc.total_allocation),
                    'allocation_by_close': {
                        str(k): str(v) for k, v in alloc.allocation_by_admitting_close.items()
                    }
                })

            if verbose and len(closes_to_process) > 1:
                self._print_aggregate_summary(aggregated, all_allocations_by_close)

        # Final summary
        if verbose:
            self._print_final_summary(grand_total_collected, grand_total_allocated)

        # Build output
        output = EngineOutput(
            fund_name=self.assumptions.fund_name,
            calculation_date=str(date.today()),
            total_late_interest_collected=str(grand_total_collected),
            total_late_interest_allocated=str(grand_total_allocated),
            new_lps=all_new_lp_results,
            existing_lps=aggregated_allocations,
            summary_by_close=close_summaries,
            settings={
                'late_interest_base': self.assumptions.late_interest_base.value,
                'late_spread': str(self.assumptions.late_spread),
                'compounding': self.assumptions.late_interest_compounding.value,
                'end_date_calculation': self.assumptions.end_date_calculation.value,
                'calc_rounding': self.assumptions.calc_rounding,
                'sum_rounding': self.assumptions.sum_rounding,
                'prime_rate': str(self.assumptions.prime_rate_history[0].rate) if self.assumptions.prime_rate_history else 'N/A'
            }
        )

        return output

    # ========================================================================
    # PRINTING UTILITIES
    # ========================================================================

    def _print_header(self, title: str):
        print("\n" + "=" * 100)
        print(title.center(100))
        print("=" * 100)

    def _print_section_header(self, title: str):
        print("\n" + "=" * 100)
        print(title)
        print("=" * 100)

    def _print_summary(self, total_partners: int, total_calls: int, closes: List[int]):
        print(f"\nFund: {self.assumptions.fund_name}")
        print(f"Total Partners: {total_partners}")
        print(f"Total Capital Calls: {total_calls}")
        print(f"Closes: {closes}")

        if self.assumptions.late_interest_base == InterestBase.PRIME:
            prime_rate = self.assumptions.prime_rate_history[0].rate if self.assumptions.prime_rate_history else Decimal('0')
            total_rate = prime_rate + self.assumptions.late_spread
            print(f"Interest Rate: Prime {prime_rate}% + Spread {self.assumptions.late_spread}% = {total_rate}%")
        else:
            print(f"Interest Rate: {self.assumptions.flat_rate}% (flat)")

    def _print_late_interest_table(self, calcs: List, total: Decimal):
        print("\n" + "-" * 100)
        print("LATE INTEREST DUE FROM NEW LPs")
        print("-" * 100)
        print(f"{'Partner':<25} {'Commitment':<20} {'Missed Calls':<15} {'Late Interest':<20}")
        print("-" * 100)

        for calc in calcs:
            missed = len(calc.breakdown_by_capital_call)
            print(f"{calc.partner_name:<25} ${calc.commitment:>18,.2f} {missed:>14} "
                  f"${calc.total_late_interest_due:>18,.2f}")

        print("-" * 100)
        print(f"{'TOTAL COLLECTED':<60} ${total:>18,.2f}")

    def _print_allocation_table(self, allocations: List, existing_partners: List[Partner], total: Decimal):
        print("\n" + "-" * 100)
        print("PRO-RATA ALLOCATION TO EXISTING LPs")
        print("-" * 100)

        total_commitment = sum(p.commitment for p in existing_partners)
        print(f"{'Partner':<25} {'Commitment':<20} {'% Ownership':<15} {'Allocation':<20}")
        print("-" * 100)

        for alloc in allocations:
            pct = (alloc.commitment / total_commitment) * Decimal('100')
            print(f"{alloc.partner_name:<25} ${alloc.commitment:>18,.2f} "
                  f"{pct:>13.2f}% ${alloc.total_allocation:>18,.2f}")

        print("-" * 100)
        print(f"{'TOTAL ALLOCATED':<61} ${total:>18,.2f}")

    def _print_balance_check(self, collected: Decimal, allocated: Decimal):
        diff = collected - allocated
        print(f"\n{'Collected:':<30} ${collected:>18,.2f}")
        print(f"{'Allocated:':<30} ${allocated:>18,.2f}")
        print(f"{'Difference:':<30} ${diff:>18,.2f}")

        if abs(diff) < Decimal('0.10'):
            print("✓ Balanced (within rounding tolerance)")
        else:
            print(f"⚠ Warning: Difference of ${diff:,.2f}")

    def _print_aggregate_summary(self, aggregated: List, by_close: Dict):
        print("\n" + "=" * 100)
        print("AGGREGATE ALLOCATION SUMMARY - ALL CLOSES")
        print("=" * 100)

        print(f"\n{'Partner':<25} {'Close':<10} ", end='')
        for close_num in sorted(by_close.keys()):
            print(f"{'Close ' + str(close_num):<20}", end='')
        print(f"{'Total':<20}")
        print("-" * 100)

        for alloc in sorted(aggregated, key=lambda a: a.close_number):
            print(f"{alloc.partner_name:<25} {alloc.close_number:<10} ", end='')
            for close_num in sorted(by_close.keys()):
                amt = alloc.allocation_by_admitting_close.get(close_num, Decimal('0'))
                print(f"${amt:>18,.2f} ", end='')
            print(f"${alloc.total_allocation:>18,.2f}")

    def _print_final_summary(self, collected: Decimal, allocated: Decimal):
        print("\n" + "=" * 100)
        print("FINAL SUMMARY")
        print("=" * 100)
        print(f"Grand Total Late Interest Collected: ${collected:>18,.2f}")
        print(f"Grand Total Late Interest Allocated:  ${allocated:>18,.2f}")
        print(f"Difference:                            ${collected - allocated:>18,.2f}")
        print("=" * 100)


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description='Late Interest Engine - Complete Calculator for Private Equity Funds',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Interactive mode
  python3 late_interest_engine.py --interactive

  # From CSV file
  python3 late_interest_engine.py --csv data.csv

  # Interactive with custom settings
  python3 late_interest_engine.py --interactive --fund-name "Fund IV" --prime-rate 8.5 --spread 3.0
        '''
    )

    parser.add_argument(
        '--csv',
        type=str,
        help='Path to CSV file with partners and capital calls'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Enter data interactively (no CSV required)'
    )

    parser.add_argument(
        '--fund-name',
        type=str,
        default='Fund',
        help='Name of the fund (default: Fund)'
    )

    parser.add_argument(
        '--prime-rate',
        type=float,
        default=7.5,
        help='Prime rate percentage (default: 7.5)'
    )

    parser.add_argument(
        '--spread',
        type=float,
        default=2.0,
        help='Spread percentage added to prime (default: 2.0)'
    )

    parser.add_argument(
        '--compounding',
        type=str,
        choices=['simple', 'compound'],
        default='simple',
        help='Interest compounding method (default: simple)'
    )

    parser.add_argument(
        '--end-date-calc',
        type=str,
        choices=['issue_date', 'due_date'],
        default='issue_date',
        help='End date calculation method (default: issue_date)'
    )

    parser.add_argument(
        '--calc-rounding',
        type=int,
        default=2,
        help='Decimal places for intermediate calculations (default: 2)'
    )

    parser.add_argument(
        '--sum-rounding',
        type=int,
        default=2,
        help='Decimal places for final sums (default: 2)'
    )

    parser.add_argument(
        '--output-json',
        type=str,
        help='Path to save JSON output'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress console output'
    )

    args = parser.parse_args()

    # Load data
    if args.interactive:
        # Interactive mode
        partners, capital_calls = interactive_input_mode()

        if not partners or not capital_calls:
            print("\nError: No data entered. Cannot proceed with calculation.")
            return 1

    elif args.csv:
        # CSV mode
        csv_path = Path(args.csv)
        if not csv_path.exists():
            print(f"Error: CSV file not found: {csv_path}")
            return 1

        partners, capital_calls = load_from_csv(str(csv_path))

        if not partners or not capital_calls:
            print("Error: Could not load data from CSV")
            return 1
    else:
        # No mode specified
        print("Error: You must specify either --interactive or --csv")
        print("\nUsage:")
        print("  python3 late_interest_engine.py --interactive")
        print("  python3 late_interest_engine.py --csv <path_to_csv>")
        print("\nFor more help, run: python3 late_interest_engine.py --help")
        return 1

    # Set up assumptions
    assumptions = FundAssumptions(
        fund_name=args.fund_name,
        late_interest_base=InterestBase.PRIME,
        late_spread=Decimal(str(args.spread)),
        prime_rate_history=[
            PrimeRateChange(effective_date=date(2020, 1, 1), rate=Decimal(str(args.prime_rate)))
        ],
        late_interest_compounding=InterestCompounding.SIMPLE if args.compounding == 'simple' else InterestCompounding.COMPOUND,
        end_date_calculation=EndDateCalculation.ISSUE_DATE if args.end_date_calc == 'issue_date' else EndDateCalculation.DUE_DATE,
        mgmt_fee_allocated_interest=False,
        allocated_to_all_existing_lps=True,
        calc_rounding=args.calc_rounding,
        sum_rounding=args.sum_rounding
    )

    # Run engine
    engine = LateInterestEngine(assumptions)
    output = engine.run_complete_calculation(
        partners=partners,
        capital_calls=capital_calls,
        verbose=not args.quiet
    )

    # Save JSON output if requested
    if args.output_json:
        with open(args.output_json, 'w') as f:
            json.dump(asdict(output), f, indent=2)

        if not args.quiet:
            print(f"\n✓ JSON output saved to: {args.output_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
