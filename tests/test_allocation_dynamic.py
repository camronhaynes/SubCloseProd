"""
Dynamic allocation test script that works with actual data.
Reads capital calls and partners from CSV/data files and calculates
late interest + allocations for any given scenario.
"""

import sys
import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Tuple

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


def parse_date(date_str: str) -> date:
    """Parse date from various formats"""
    if not date_str or date_str.strip() == '':
        return None

    # Try different date formats
    formats = ['%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Could not parse date: {date_str}")


def parse_currency(value: str) -> Decimal:
    """Parse currency string to Decimal"""
    if not value or value.strip() in ['', '-', '$-', '$   -']:
        return Decimal('0')

    # Remove currency symbols, commas, spaces
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


def load_partners_from_csv(csv_path: str) -> List[Partner]:
    """
    Load partners from CSV file.

    Expected CSV format:
    Partner,Issue Date,Commitment,Close
    Partner 1,04/04/2022,250000,1
    Partner 2,08/17/2022,500000,1
    """
    partners = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty rows
            if not row.get('Partner') or row['Partner'].strip() == '':
                continue

            try:
                partner = Partner(
                    name=row['Partner'].strip(),
                    issue_date=parse_date(row['Issue Date']),
                    commitment=parse_currency(row['Commitment']),
                    close_number=int(row['Close'])
                )

                if partner.commitment > 0:  # Only add partners with actual commitments
                    partners.append(partner)
            except Exception as e:
                print(f"Warning: Could not parse partner row: {row}. Error: {e}")
                continue

    return partners


def load_capital_calls_from_csv(csv_path: str) -> List[CapitalCall]:
    """
    Load capital calls from CSV file.

    Expected CSV format:
    Call Number,Due Date,Call %
    1,4/20/22,20.00%
    2,1/23/23,10.00%
    """
    capital_calls = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty rows
            if not row.get('Call Number') or row['Call Number'].strip() == '':
                continue

            try:
                call = CapitalCall(
                    call_number=int(row['Call Number']),
                    due_date=parse_date(row['Due Date']),
                    call_percentage=parse_percentage(row['Call %'])
                )
                capital_calls.append(call)
            except Exception as e:
                print(f"Warning: Could not parse capital call row: {row}. Error: {e}")
                continue

    return capital_calls


def extract_data_from_late_interest_csv(csv_path: str) -> Tuple[List[Partner], List[CapitalCall]]:
    """
    Extract partners and capital calls from the ex late interest tab.csv format.
    This is a complex CSV with data in specific locations.
    """
    partners = []
    capital_calls = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        lines = list(csv.reader(f))

    # Parse capital calls from header rows
    # Row 0 (index 0): "Cap Call", call_number, "Cap Call", call_number, ...
    # Row 1 (index 1): "Due Date", actual_date, "Due Date", actual_date, ...
    # Row 2 (index 2): "Call %", percentage, "Call %", percentage, ...

    if len(lines) > 2:
        header_row = lines[0]
        due_date_row = lines[1]
        call_pct_row = lines[2]

        # Find "Cap Call" entries and extract call number
        i = 0
        while i < len(header_row):
            cell = header_row[i]
            if cell and 'Cap Call' in cell:
                # Next cell should be the call number
                if i + 1 < len(header_row):
                    try:
                        call_num_str = header_row[i + 1].strip()
                        if call_num_str.isdigit():
                            call_num = int(call_num_str)

                            # Due date should be in due_date_row at i+1
                            due_date_str = due_date_row[i + 1] if i + 1 < len(due_date_row) else ''
                            # Call % should be in call_pct_row at i+1
                            call_pct_str = call_pct_row[i + 1] if i + 1 < len(call_pct_row) else ''

                            if due_date_str and call_pct_str:
                                try:
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
                    except:
                        pass
            i += 1

    # Parse new LP from row 4 (index 4) if present
    if len(lines) > 4:
        new_lp_row = lines[4]
        if len(new_lp_row) > 4:
            try:
                partner_name = new_lp_row[1].strip() if new_lp_row[1] else ''
                issue_date_str = new_lp_row[2] if len(new_lp_row) > 2 else ''
                commitment_str = new_lp_row[3] if len(new_lp_row) > 3 else ''
                close_str = new_lp_row[4] if len(new_lp_row) > 4 else ''

                if partner_name and partner_name not in ['', 'Partner']:
                    issue_date = parse_date(issue_date_str) if issue_date_str else None
                    commitment = parse_currency(commitment_str)
                    close_num = int(close_str.strip()) if close_str and close_str.strip().isdigit() else 2

                    if commitment > 0 and issue_date:
                        partners.append(Partner(
                            name=partner_name,
                            issue_date=issue_date,
                            commitment=commitment,
                            close_number=close_num
                        ))
            except Exception as e:
                pass

    # Parse existing partners starting from row 18 (index 18)
    for i in range(18, len(lines)):
        row = lines[i]

        if len(row) < 4:
            continue

        # Check if this is a partner row (has a partner name in column 1)
        partner_name = row[1].strip() if len(row) > 1 else ''
        if not partner_name or partner_name == 'Partner' or partner_name == '':
            continue

        try:
            issue_date_str = row[2] if len(row) > 2 else ''
            commitment_str = row[3] if len(row) > 3 else ''
            close_str = row[4] if len(row) > 4 else ''

            issue_date = parse_date(issue_date_str) if issue_date_str else None
            commitment = parse_currency(commitment_str)
            close_num = int(close_str.strip()) if close_str and close_str.strip().isdigit() else 1

            if commitment > 0:
                partners.append(Partner(
                    name=partner_name,
                    issue_date=issue_date if issue_date else date(2022, 4, 1),
                    commitment=commitment,
                    close_number=close_num
                ))
        except Exception as e:
            continue

    return partners, capital_calls


def run_dynamic_allocation_test(
    partners: List[Partner],
    capital_calls: List[CapitalCall],
    assumptions: FundAssumptions,
    target_close: int = None
):
    """
    Run allocation calculation for any set of partners and capital calls.

    Args:
        partners: List of all partners
        capital_calls: List of all capital calls
        assumptions: Fund assumptions
        target_close: Specific close to analyze (None = analyze all)
    """

    # Sort partners by close
    partners.sort(key=lambda p: p.close_number)

    # Group partners by close
    partners_by_close: Dict[int, List[Partner]] = {}
    for partner in partners:
        if partner.close_number not in partners_by_close:
            partners_by_close[partner.close_number] = []
        partners_by_close[partner.close_number].append(partner)

    # Determine which closes to process
    all_closes = sorted(partners_by_close.keys())
    if target_close:
        closes_to_process = [c for c in all_closes if c == target_close]
    else:
        closes_to_process = all_closes[1:]  # Skip first close (no late interest)

    print("=" * 100)
    print("DYNAMIC ALLOCATION TEST - PROCESSING ALL CLOSES")
    print("=" * 100)

    print(f"\nFund Setup:")
    print(f"  Total Partners: {len(partners)}")
    print(f"  Total Capital Calls: {len(capital_calls)}")
    print(f"  Closes: {all_closes}")
    print(f"  Interest Rate: Prime {assumptions.prime_rate_history[0].rate}% + {assumptions.late_spread}% = "
          f"{assumptions.prime_rate_history[0].rate + assumptions.late_spread}%")

    # Initialize calculators
    late_calc = LateInterestCalculator(assumptions)
    alloc_calc = AllocationCalculator(assumptions)

    # Track all allocations across closes
    all_allocations_by_close = {}
    grand_total_collected = Decimal('0')
    grand_total_allocated = Decimal('0')

    # Process each close
    for close_num in closes_to_process:
        print("\n" + "=" * 100)
        print(f"CLOSE {close_num}")
        print("=" * 100)

        # Get new LPs at this close
        new_lps_at_close = partners_by_close[close_num]

        # Get existing partners (all from prior closes)
        existing_partners = [p for p in partners if p.close_number < close_num]

        print(f"\nNew LPs joining at Close {close_num}: {len(new_lps_at_close)}")
        for lp in new_lps_at_close:
            print(f"  - {lp.name}: ${lp.commitment:,.2f}")

        print(f"\nExisting LPs (for allocation): {len(existing_partners)}")
        for lp in existing_partners:
            print(f"  - {lp.name}: ${lp.commitment:,.2f} (Close {lp.close_number})")

        # Calculate late interest for each new LP
        new_lp_calcs = []
        total_collected = Decimal('0')

        print("\n" + "-" * 100)
        print("LATE INTEREST CALCULATIONS")
        print("-" * 100)
        print(f"{'Partner':<20} {'Commitment':<20} {'Missed Calls':<15} {'Late Interest':<20}")
        print("-" * 100)

        for new_lp in new_lps_at_close:
            calc = late_calc.calculate_late_interest_for_new_lp(new_lp, capital_calls)
            new_lp_calcs.append(calc)
            total_collected += calc.total_late_interest_due

            missed_calls = len(calc.breakdown_by_capital_call)
            print(f"{new_lp.name:<20} ${new_lp.commitment:>18,.2f} {missed_calls:>14} "
                  f"${calc.total_late_interest_due:>18,.2f}")

        print("-" * 100)
        print(f"{'TOTAL COLLECTED':<55} ${total_collected:>18,.2f}")

        grand_total_collected += total_collected

        # Calculate allocations
        if existing_partners and total_collected > 0:
            allocations, total_allocated = alloc_calc.calculate_allocations(
                new_lps=new_lp_calcs,
                all_partners=partners,
                admitting_close_number=close_num
            )

            all_allocations_by_close[close_num] = allocations
            grand_total_allocated += total_allocated

            # Display allocations
            print("\n" + "-" * 100)
            print("PRO-RATA ALLOCATION TO EXISTING LPs")
            print("-" * 100)

            total_existing_commitment = sum(p.commitment for p in existing_partners)
            print(f"{'Partner':<20} {'Commitment':<20} {'% Ownership':<15} {'Allocation':<20}")
            print("-" * 100)

            for alloc in allocations:
                pct = (alloc.commitment / total_existing_commitment) * Decimal('100')
                print(f"{alloc.partner_name:<20} ${alloc.commitment:>18,.2f} "
                      f"{pct:>13.2f}% ${alloc.total_allocation:>18,.2f}")

            print("-" * 100)
            print(f"{'TOTAL ALLOCATED':<56} ${total_allocated:>18,.2f}")

            # Verify balance
            diff = total_collected - total_allocated
            print(f"\n{'Collected:':<30} ${total_collected:>18,.2f}")
            print(f"{'Allocated:':<30} ${total_allocated:>18,.2f}")
            print(f"{'Difference:':<30} ${diff:>18,.2f}")

            if abs(diff) < Decimal('0.10'):
                print("✓ Balanced (within rounding tolerance)")
            else:
                print(f"⚠ Warning: Difference of ${diff:,.2f}")
        else:
            print("\n(No existing partners to allocate to)")

    # Summary across all closes
    if len(closes_to_process) > 1 and all_allocations_by_close:
        print("\n\n" + "=" * 100)
        print("AGGREGATE SUMMARY - ALL CLOSES")
        print("=" * 100)

        aggregated = alloc_calc.aggregate_allocations_across_closes(all_allocations_by_close)

        print("\n" + "-" * 100)
        print(f"{'Partner':<20} {'Close':<10} ", end='')
        for close_num in sorted(all_allocations_by_close.keys()):
            print(f"{'Close ' + str(close_num):<20}", end='')
        print(f"{'Total Allocation':<20}")
        print("-" * 100)

        for alloc in sorted(aggregated, key=lambda a: a.close_number):
            print(f"{alloc.partner_name:<20} {alloc.close_number:<10} ", end='')
            for close_num in sorted(all_allocations_by_close.keys()):
                amt = alloc.allocation_by_admitting_close.get(close_num, Decimal('0'))
                print(f"${amt:>18,.2f} ", end='')
            print(f"${alloc.total_allocation:>18,.2f}")

        print("-" * 100)
        print(f"\n{'Grand Total Collected:':<30} ${grand_total_collected:>18,.2f}")
        print(f"{'Grand Total Allocated:':<30} ${grand_total_allocated:>18,.2f}")
        print(f"{'Difference:':<30} ${grand_total_collected - grand_total_allocated:>18,.2f}")


if __name__ == "__main__":
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

    # Try to load from the ex late interest CSV
    csv_path = Path(__file__).parent / "ex late interest tab.csv"

    if csv_path.exists():
        print("Loading data from: ex late interest tab.csv")
        partners, capital_calls = extract_data_from_late_interest_csv(str(csv_path))

        if partners and capital_calls:
            run_dynamic_allocation_test(partners, capital_calls, assumptions)
        else:
            print("Error: Could not extract data from CSV")
    else:
        print(f"CSV file not found: {csv_path}")
        print("\nTo use this script:")
        print("1. Create a CSV with partners (columns: Partner, Issue Date, Commitment, Close)")
        print("2. Create a CSV with capital calls (columns: Call Number, Due Date, Call %)")
        print("3. Or provide data in the 'ex late interest tab.csv' format")
