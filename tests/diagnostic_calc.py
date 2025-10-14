"""
Diagnostic script to reverse-engineer the exact Excel formula
"""

from datetime import date
from decimal import Decimal

# Test with the first capital call
due_date = date(2022, 4, 20)
issue_date = date(2025, 10, 31)
capital = Decimal('1000000.00')
rate = Decimal('9.25')  # 9.25%
expected_interest = Decimal('336013.70')

# Calculate days (inclusive)
days = (issue_date - due_date).days + 1
print(f"Days (inclusive): {days}")
print(f"Capital: ${capital:,.2f}")
print(f"Rate: {rate}%")
print(f"Expected Interest: ${expected_interest:,.2f}")
print()

# Try different formulas
print("Testing different calculation methods:")
print("-" * 60)

# Method 1: Standard simple interest (rate / 100)
interest_1 = capital * (rate / Decimal('100')) * (Decimal(days) / Decimal('365'))
print(f"Method 1 (rate/100): ${interest_1:,.2f} - Diff: ${interest_1 - expected_interest:,.2f}")

# Method 2: Rate already as decimal (but that doesn't make sense with 9.25)
interest_2 = capital * rate * (Decimal(days) / Decimal('365'))
print(f"Method 2 (rate as is): ${interest_2:,.2f} - Diff: ${interest_2 - expected_interest:,.2f}")

# Method 3: What if Excel stores 9.25% as 0.0925 but displays as 9.25?
rate_decimal = Decimal('0.0925')
interest_3 = capital * rate_decimal * (Decimal(days) / Decimal('365'))
print(f"Method 3 (0.0925): ${interest_3:,.2f} - Diff: ${interest_3 - expected_interest:,.2f}")

# Method 4: Reverse calculate what rate would produce the expected result
# expected_interest = capital * rate * (days / 365)
# rate = expected_interest * 365 / (capital * days)
implied_rate = expected_interest * Decimal('365') / (capital * Decimal(days))
print(f"\nImplied rate from expected result: {implied_rate:.10f}")
print(f"Implied rate as percentage: {implied_rate * 100:.10f}%")

# Method 5: What if there's an off-by-one in days?
days_exclusive = (issue_date - due_date).days
interest_5 = capital * (rate / Decimal('100')) * (Decimal(days_exclusive) / Decimal('365'))
print(f"\nMethod 5 (exclusive days {days_exclusive}): ${interest_5:,.2f} - Diff: ${interest_5 - expected_interest:,.2f}")

# Method 6: What about 360-day year convention?
interest_6 = capital * (rate / Decimal('100')) * (Decimal(days) / Decimal('360'))
print(f"Method 6 (360-day year): ${interest_6:,.2f} - Diff: ${interest_6 - expected_interest:,.2f}")

# Method 7: Different rounding
interest_7_unrounded = capital * (rate / Decimal('100')) * (Decimal(days) / Decimal('365'))
interest_7_round2 = interest_7_unrounded.quantize(Decimal('0.01'))
print(f"\nMethod 7 (round to 2): ${interest_7_round2:,.2f} - Diff: ${interest_7_round2 - expected_interest:,.2f}")

# Try to find the exact formula by working backwards more precisely
print("\n" + "=" * 60)
print("Detailed reverse engineering:")
print("=" * 60)

# What's the actual rate being used?
# expected = capital * effective_rate * (days / 365)
# effective_rate = expected * 365 / (capital * days)
effective_annual_rate = expected_interest * Decimal('365') / (capital * Decimal(days))
print(f"Effective annual rate (as decimal): {effective_annual_rate}")
print(f"Effective annual rate (as %): {effective_annual_rate * Decimal('100')}%")
print(f"Our rate: {rate}% = {rate / Decimal('100')} as decimal")
print(f"Difference: {(effective_annual_rate - rate / Decimal('100')) * Decimal('100')}%")
