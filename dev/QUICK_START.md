# Quick Start Guide - Interactive Mode

## Run Interactive Mode

```bash
python3 late_interest_engine.py --interactive
```

## Example: Simple Scenario

**Scenario:** $10M fund, 3 capital calls, 1 new investor at subsequent close

### Step 1: Enter Capital Calls

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

Type: done
```

### Step 2: Enter Partners

```
Partner #1 (Existing LP - Close 1):
  Partner name: ABC Partners
  Commitment: 5m
  Issue date: [press Enter]
  Close number: 1

Partner #2 (Existing LP - Close 1):
  Partner name: XYZ Capital
  Commitment: 5m
  Issue date: [press Enter]
  Close number: 1

Partner #3 (New LP - Close 2):
  Partner name: New Investor
  Commitment: 3m
  Issue date: 7/1/22
  Close number: 2

Type: done
```

### Step 3: Review & Confirm

- Review the summary
- Type `y` to proceed

### Result

The engine calculates:
- Late interest from New Investor (missed calls 1 & 2)
- Allocates it pro-rata to ABC Partners and XYZ Capital
- Shows detailed breakdown

## Natural Language Cheat Sheet

### Amounts
- `10m` = $10,000,000
- `5.5m` = $5,500,000
- `500k` = $500,000

### Dates
- `1/15/22` ✓
- `Jan 15 2022` ✓
- `2023-01-15` ✓

## Understanding Close Numbers

- **Close 1**: Initial close (existing LPs)
  - These LPs do NOT pay late interest
  - They RECEIVE allocations from new LPs

- **Close 2+**: Subsequent close (new LPs)
  - These LPs PAY late interest on missed capital calls
  - Late interest is allocated to Close 1 LPs

## Common Use Cases

### 1. Single Subsequent Close
- Multiple Close 1 LPs
- 1 or more Close 2 LPs

### 2. Multiple Subsequent Closes
- Close 1 LPs (existing)
- Close 2 LPs (pay late interest on calls 1+)
- Close 3 LPs (pay late interest on calls 1, 2, etc.)

### 3. Custom Settings

```bash
# Higher interest rate
python3 late_interest_engine.py --interactive --prime-rate 8.5 --spread 3.0

# Compound interest
python3 late_interest_engine.py --interactive --compounding compound

# Save results to JSON
python3 late_interest_engine.py --interactive --output-json results.json
```

## Need Help?

```bash
# Full help
python3 late_interest_engine.py --help

# See examples
python3 late_interest_engine.py --help | grep -A 10 "Examples"

# Run test
python3 test_programmatic.py
```
