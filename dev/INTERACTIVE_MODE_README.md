# Late Interest Engine - Interactive Mode

The Late Interest Engine now supports **interactive mode** where you can input data directly without needing a CSV file. This makes it easy to quickly calculate late interest for various scenarios.

## Quick Start

Run the interactive mode:

```bash
python3 late_interest_engine.py --interactive
```

## Features

### Natural Language Input Support

The engine understands natural language inputs for currency amounts:

| Input | Parsed Value |
|-------|--------------|
| `10m` or `10M` | $10,000,000 |
| `5.5m` | $5,500,000 |
| `500k` | $500,000 |
| `2.5k` | $2,500 |
| `$10,000,000` | $10,000,000 |

### Flexible Date Formats

Dates can be entered in multiple formats:

- `1/15/23` or `01/15/2022`
- `Jan 15 2023` or `January 15, 2023`
- `2023-01-15`

## Usage Examples

### Example 1: Basic Interactive Session

```bash
python3 late_interest_engine.py --interactive
```

The system will prompt you for:

1. **Capital Calls**
   - Due date for each capital call
   - Call percentage
   - Type `done` when finished

2. **Partners/LPs**
   - Partner name
   - Commitment amount (use natural language like "10m")
   - Issue date (optional, defaults to first capital call)
   - Close number (1 for initial close, 2+ for subsequent closes)
   - Type `done` when finished

### Example 2: Interactive with Custom Settings

```bash
python3 late_interest_engine.py --interactive \
  --fund-name "Fund IV" \
  --prime-rate 8.5 \
  --spread 3.0 \
  --compounding compound
```

### Example 3: Sample Data Entry

**Scenario:** Fund with $10M in commitments, 3 capital calls, 1 subsequent close investor

**Capital Calls:**
```
Capital Call #1:
  Due date: 1/15/22
  Call percentage: 10

Capital Call #2:
  Due date: 6/15/22
  Call percentage: 15

Capital Call #3:
  Due date: 12/15/22
  Call percentage: 20

Type 'done'
```

**Partners:**
```
Partner #1 (Existing LP):
  Partner name: ABC Partners
  Commitment: 5m
  Issue date: [press Enter]
  Close number: 1

Partner #2 (Existing LP):
  Partner name: XYZ Capital
  Commitment: 5m
  Issue date: [press Enter]
  Close number: 1

Partner #3 (New LP at subsequent close):
  Partner name: New Investor LLC
  Commitment: 3m
  Issue date: 7/1/22
  Close number: 2

Type 'done'
```

**Output:** The engine will calculate:
- Late interest owed by "New Investor LLC" (who missed calls 1 & 2)
- Pro-rata allocation to existing LPs ("ABC Partners" & "XYZ Capital")
- Detailed breakdown by capital call

## Command Line Options

### Data Input Options
- `--interactive` - Enter data interactively (no CSV required)
- `--csv <path>` - Load data from CSV file

### Fund Settings
- `--fund-name <name>` - Name of the fund (default: "Fund")
- `--prime-rate <rate>` - Prime rate percentage (default: 7.5)
- `--spread <rate>` - Spread added to prime rate (default: 2.0)
- `--compounding {simple,compound}` - Interest compounding method (default: simple)
- `--end-date-calc {issue_date,due_date}` - End date calculation method (default: issue_date)

### Output Options
- `--output-json <path>` - Save results to JSON file
- `--quiet` - Suppress console output

### Advanced Options
- `--calc-rounding <digits>` - Decimal places for calculations (default: 2)
- `--sum-rounding <digits>` - Decimal places for final sums (default: 2)

## Programmatic Usage

You can also use the engine programmatically in Python:

```python
from late_interest_engine import LateInterestEngine, parse_natural_currency
from app.models.data_models import Partner, CapitalCall, FundAssumptions
from datetime import date
from decimal import Decimal

# Parse natural language amounts
commitment = parse_natural_currency("10m")  # Returns Decimal('10000000')

# Create partners and capital calls
partners = [
    Partner(name="ABC Partners", issue_date=date(2022, 1, 15),
            commitment=Decimal('5000000'), close_number=1),
    Partner(name="New LP", issue_date=date(2022, 7, 1),
            commitment=Decimal('3000000'), close_number=2),
]

capital_calls = [
    CapitalCall(call_number=1, due_date=date(2022, 1, 15),
                call_percentage=Decimal('10')),
]

# Set up fund assumptions and run calculation
assumptions = FundAssumptions(...)
engine = LateInterestEngine(assumptions)
output = engine.run_complete_calculation(partners, capital_calls)
```

See `test_programmatic.py` for a complete example.

## How It Works

### Late Interest Calculation

When an LP joins at a **subsequent close**, they must pay "late interest" on the capital they would have contributed if they had joined at the initial close.

**For each missed capital call:**
- Calculate: `Capital Amount × Interest Rate × Days Late / 365`
- Capital Amount = Commitment × Call Percentage
- Interest Rate = Prime Rate + Spread (e.g., 7.5% + 2.0% = 9.5%)
- Days Late = Days from capital call due date to LP's issue date

### Pro-Rata Allocation

The late interest collected from new LPs is allocated **pro-rata** to existing LPs based on their ownership percentage:

```
Allocation = Total Late Interest × (LP's Commitment / Total Existing Commitments)
```

### Example Calculation

**Given:**
- New LP: $3M commitment, joins 7/1/22 (Close 2)
- Existing LPs: $10M total commitment (Close 1)
- Missed Call #1: 10% on 1/15/22 = $300K capital
- Days late: 167 days
- Rate: 9.5%

**Late Interest:**
- $300,000 × 9.5% × 167/365 = $13,042.47

**Allocation to Existing LPs:**
- If existing LP has $5M commitment (50% ownership)
- Allocation = $13,042.47 × 50% = $6,521.24

## Tips

1. **Natural Language**: Use "10m" for millions, "500k" for thousands
2. **Close Numbers**:
   - Close 1 = Initial close (existing LPs)
   - Close 2+ = Subsequent close (new LPs who pay late interest)
3. **Issue Date**: For initial close LPs, press Enter to use the first capital call date
4. **Review Summary**: Always review the input summary before confirming

## Getting Help

```bash
# Show all options
python3 late_interest_engine.py --help

# View examples
python3 late_interest_engine.py --help | grep -A 10 "Examples:"
```

## Testing

Run the test script to see a complete example:

```bash
python3 test_programmatic.py
```

This will demonstrate:
- Natural language parsing
- A complete calculation with 3 capital calls
- Late interest calculation for a subsequent close LP
- Pro-rata allocation to existing LPs
