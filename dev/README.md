# Late Interest Engine - Complete Documentation

## Overview

The Late Interest Engine is a comprehensive Python-based calculator for private equity fund subsequent close calculations. It handles late interest calculations for new LPs joining at subsequent closes and pro-rata allocations to existing LPs.

## Key Features

✅ **Late Interest Calculations**
- Simple and compound interest methods
- Variable rates (Prime + spread) or flat rates
- Inclusive day counting (Excel-compatible)
- Historical rate change support
- Configurable rounding

✅ **Pro-Rata Allocation**
- Automatic allocation to existing LPs based on ownership percentage
- Multi-close aggregation
- Edge case handling (commitment increases)

✅ **Flexible Input**
- CSV file parsing
- Programmatic API
- Multiple date formats
- Currency parsing

✅ **Complete Output**
- Console display with formatted tables
- JSON export for integration
- Detailed breakdowns per capital call
- Summary by close

## File Structure

```
SubCloseProd/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── data_models.py          # Core data models
│   │   └── calculators/
│   │       ├── interest_rate_calculator.py    # Interest calculations
│   │       ├── late_interest_calculator.py    # Late interest logic
│   │       └── allocation_calculator.py       # Pro-rata allocation
│   └── ...
├── late_interest_engine.py              # 🚀 MAIN ENGINE (unified script)
├── test_late_interest_historical.py     # Historical validation tests
├── test_allocation_dynamic.py           # Dynamic allocation tests
├── ex late interest tab.csv             # Sample data file
└── README.md                            # This file
```

## Quick Start

### Command Line Usage

```bash
# Basic usage with CSV file
python3 late_interest_engine.py --csv "ex late interest tab.csv"

# With custom settings
python3 late_interest_engine.py \
  --csv "ex late interest tab.csv" \
  --fund-name "My Fund" \
  --prime-rate 7.5 \
  --spread 2.0 \
  --compounding simple \
  --output-json results.json

# Quiet mode (JSON only)
python3 late_interest_engine.py \
  --csv "ex late interest tab.csv" \
  --output-json results.json \
  --quiet
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--csv` | Path to CSV file with partners and capital calls | **Required** |
| `--fund-name` | Name of the fund | `"Fund"` |
| `--prime-rate` | Prime rate percentage | `7.5` |
| `--spread` | Spread percentage added to prime | `2.0` |
| `--compounding` | Interest compounding method (`simple` or `compound`) | `simple` |
| `--end-date-calc` | End date calculation (`issue_date` or `due_date`) | `issue_date` |
| `--calc-rounding` | Decimal places for intermediate calculations | `2` |
| `--sum-rounding` | Decimal places for final sums | `2` |
| `--output-json` | Path to save JSON output | None |
| `--quiet` | Suppress console output | False |

### Programmatic Usage

```python
from late_interest_engine import LateInterestEngine, load_from_csv
from app.models.data_models import FundAssumptions, PrimeRateChange, InterestBase, InterestCompounding, EndDateCalculation
from decimal import Decimal
from datetime import date

# Load data from CSV
partners, capital_calls = load_from_csv("ex late interest tab.csv")

# Set up fund assumptions
assumptions = FundAssumptions(
    fund_name="My Fund",
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

# Run calculation
engine = LateInterestEngine(assumptions)
output = engine.run_complete_calculation(
    partners=partners,
    capital_calls=capital_calls,
    verbose=True  # Print detailed output
)

# Access results
print(f"Total collected: ${output.total_late_interest_collected}")
print(f"Total allocated: ${output.total_late_interest_allocated}")

for new_lp in output.new_lps:
    print(f"{new_lp['partner_name']}: ${new_lp['total_late_interest_due']}")

for existing_lp in output.existing_lps:
    print(f"{existing_lp['partner_name']}: ${existing_lp['total_allocation']}")
```

## CSV File Format

The engine expects a CSV file in the "ex late interest tab" format:

**Row 1:** Capital call headers
```
..., Cap Call, 1, Cap Call, 2, ...
```

**Row 2:** Due dates
```
..., Due Date, 4/20/22, Due Date, 1/23/23, ...
```

**Row 3:** Call percentages
```
..., Call %, 20.00%, Call %, 10.00%, ...
```

**Row 5+:** New LP data (optional)
```
SubClose Due Date, Partner, Issue Date, Commitment, Close, ...
10/31/25, New LP, 10/31/25, $5,000,000.00, 2, ...
```

**Row 19+:** Existing LP data
```
, Partner, Issue Date, Commitment, Close, ...
, Partner 1, 04/04/2022, 250000, 1, ...
, Partner 2, 08/17/2022, 500000, 1, ...
```

## Calculation Methodology

### Late Interest Formula (Simple Interest)

```
Interest = Principal × (Rate / 100) × ((End Date - Start Date + 1) / 365)
```

**Key Points:**
- **Inclusive day counting**: Both start and end dates are included (+1)
- **365-day year**: Standard day count convention
- **Rate as percentage**: e.g., 9.5 means 9.5%

### Pro-Rata Allocation

```
Allocation per LP = Total Late Interest × (LP Commitment / Total Existing Commitment)
```

**Example:**
- Total late interest collected: $704,223.29
- Partner A commitment: $1,000,000
- Total existing commitments: $23,750,000
- Partner A allocation: $704,223.29 × ($1,000,000 / $23,750,000) = $29,626.56

### Edge Case: Commitment Increases

When an existing LP increases their commitment at a subsequent close:

1. **They PAY late interest** on the INCREASE amount (as a "new" LP)
2. **They RECEIVE allocation** on their ORIGINAL commitment (as an "existing" LP)

**Example:**
- Partner A joined Close 1 with $1M
- Partner A increases to $2M at Close 2 (+$1M increase)
- Partner A pays late interest on $1M increase
- Partner A receives allocation based on $1M original commitment
- Net: Partner A allocates some interest to themselves

## Output Structure

### Console Output

```
====================================================================================================
                            LATE INTEREST ENGINE - COMPLETE CALCULATION
====================================================================================================

Fund: Test Fund
Total Partners: 53
Total Capital Calls: 6
Closes: [1, 2]
Interest Rate: Prime 7.5% + Spread 2.0% = 9.5%

====================================================================================================
CLOSE 2
====================================================================================================

----------------------------------------------------------------------------------------------------
LATE INTEREST DUE FROM NEW LPs
----------------------------------------------------------------------------------------------------
Partner                   Commitment           Missed Calls    Late Interest
----------------------------------------------------------------------------------------------------
New LP                    $      5,000,000.00              6 $        704,223.29
----------------------------------------------------------------------------------------------------
TOTAL COLLECTED                                              $        704,223.29

----------------------------------------------------------------------------------------------------
PRO-RATA ALLOCATION TO EXISTING LPs
----------------------------------------------------------------------------------------------------
Partner                   Commitment           % Ownership     Allocation
----------------------------------------------------------------------------------------------------
Partner 1                 $        250,000.00          1.05% $          7,406.64
Partner 2                 $        500,000.00          2.10% $         14,813.28
...
```

### JSON Output

```json
{
  "fund_name": "Test Fund",
  "calculation_date": "2025-10-13",
  "total_late_interest_collected": "704223.29",
  "total_late_interest_allocated": "704223.33",
  "new_lps": [
    {
      "partner_name": "New LP",
      "close_number": 2,
      "commitment": "5000000.00",
      "total_late_interest_due": "704223.29",
      "breakdown": [
        {
          "call_number": 1,
          "capital_amount": "1000000.00",
          "late_interest": "336013.70",
          "days_late": 1290
        }
      ]
    }
  ],
  "existing_lps": [
    {
      "partner_name": "Partner 1",
      "total_allocation": "7406.64",
      "allocation_by_close": { "2": "7406.64" }
    }
  ]
}
```

## Testing

### Run Historical Validation

Validates calculations against known historical data:

```bash
python3 test_late_interest_historical.py
```

Expected output: ✓ All calculations match historical data perfectly!

### Run Dynamic Allocation Tests

Tests allocation logic with various scenarios:

```bash
python3 test_allocation_dynamic.py
```

## Technical Notes

### Rounding Behavior

- **calc_rounding**: Applied to intermediate calculations (per capital call)
- **sum_rounding**: Applied to final totals
- **Rounding method**: ROUND_HALF_UP (0.5 rounds up)

### Day Count Convention

The engine uses **inclusive day counting** to match Excel/historical behavior:
- Formula: `(end_date - start_date).days + 1`
- This includes both the start and end dates in the calculation

### Prime Rate Changes

Support for variable rates over time:

```python
prime_rate_history=[
    PrimeRateChange(effective_date=date(2020, 1, 1), rate=Decimal('7.5')),
    PrimeRateChange(effective_date=date(2023, 6, 1), rate=Decimal('8.0')),
]
```

The calculator automatically segments interest periods when the prime rate changes.

## Validation Results

The engine has been validated against historical data:

| Capital Call | Expected Interest | Calculated Interest | Match |
|--------------|-------------------|---------------------|-------|
| Call 1       | $336,013.70       | $336,013.70         | ✓     |
| Call 2       | $131,828.77       | $131,828.77         | ✓     |
| Call 3       | $32,950.68        | $32,950.68          | ✓     |
| Call 4       | $131,854.79       | $131,854.79         | ✓     |
| Call 5       | $26,092.47        | $26,092.47          | ✓     |
| Call 6       | $45,482.88        | $45,482.88          | ✓     |
| **Total**    | **$704,223.29**   | **$704,223.29**     | **✓** |

## Support

For questions or issues, please refer to the code documentation or contact the development team.

## License

Private - Proprietary Software

---

**Version:** 1.0
**Last Updated:** October 2025
**Author:** Claude Code + SubCloseProd Team
