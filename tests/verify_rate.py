"""
Verify the actual rate used in historical calculations
"""

from datetime import date
from decimal import Decimal

test_cases = [
    {
        'call': 1,
        'due_date': date(2022, 4, 20),
        'capital': Decimal('1000000.00'),
        'expected_interest': Decimal('336013.70')
    },
    {
        'call': 2,
        'due_date': date(2023, 1, 23),
        'capital': Decimal('500000.00'),
        'expected_interest': Decimal('131828.77')
    },
    {
        'call': 3,
        'due_date': date(2023, 7, 11),
        'capital': Decimal('150000.00'),
        'expected_interest': Decimal('32950.68')
    },
    {
        'call': 4,
        'due_date': date(2024, 3, 15),
        'capital': Decimal('850000.00'),
        'expected_interest': Decimal('131854.79')
    },
    {
        'call': 5,
        'due_date': date(2024, 9, 26),
        'capital': Decimal('250000.00'),
        'expected_interest': Decimal('26092.47')
    },
    {
        'call': 6,
        'due_date': date(2025, 3, 13),
        'capital': Decimal('750000.00'),
        'expected_interest': Decimal('45482.88')
    },
]

issue_date = date(2025, 10, 31)

print("=" * 80)
print("REVERSE ENGINEERING ACTUAL RATE FROM HISTORICAL DATA")
print("=" * 80)
print()

rates_found = []

for tc in test_cases:
    days = (issue_date - tc['due_date']).days + 1

    # Reverse calculate: rate = interest * 365 / (capital * days)
    implied_rate_decimal = tc['expected_interest'] * Decimal('365') / (tc['capital'] * Decimal(days))
    implied_rate_pct = implied_rate_decimal * Decimal('100')

    rates_found.append(implied_rate_pct)

    print(f"Call {tc['call']}:")
    print(f"  Days (inclusive): {days}")
    print(f"  Capital: ${tc['capital']:,.2f}")
    print(f"  Expected Interest: ${tc['expected_interest']:,.2f}")
    print(f"  Implied Rate: {implied_rate_pct:.6f}%")

    # Test with that rate
    test_interest = tc['capital'] * implied_rate_decimal * (Decimal(days) / Decimal('365'))
    print(f"  Verification: ${test_interest:,.2f}")
    print()

# Calculate average rate
avg_rate = sum(rates_found) / len(rates_found)
print("=" * 80)
print(f"Average implied rate across all calls: {avg_rate:.6f}%")
print()
print("If Prime = 7.5% and Spread = 2%, then Total = 9.5%")
print("If Prime = 7.25% and Spread = 2%, then Total = 9.25%")
print()
print(f"The historical data appears to use: {avg_rate:.2f}%")
print("=" * 80)
