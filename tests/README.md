# Test Scripts

This directory contains Python test scripts and diagnostic tools for validating the late interest calculation engine.

---

## Test Scripts

### `test_allocation.py`
**Purpose**: Tests basic pro-rata allocation calculations

**What it tests**:
- Allocation of late interest to existing LPs
- Pro-rata percentage calculations
- Multi-close scenarios

**Run**:
```bash
python3 tests/test_allocation.py
```

---

### `test_allocation_dynamic.py`
**Purpose**: Tests dynamic allocation scenarios with varying partner counts

**What it tests**:
- Multiple new LPs across different closes
- Complex allocation scenarios
- Edge cases with different commitment amounts

**Run**:
```bash
python3 tests/test_allocation_dynamic.py
```

---

### `test_late_interest_historical.py`
**Purpose**: Tests interest calculations with historical data

**What it tests**:
- Long time period calculations
- Date range accuracy
- Interest accrual over multiple years

**Run**:
```bash
python3 tests/test_late_interest_historical.py
```

---

### `test_programmatic.py`
**Purpose**: Tests programmatic API usage of the engine

**What it tests**:
- Direct API calls to calculation engine
- Data model validation
- JSON output format

**Run**:
```bash
python3 tests/test_programmatic.py
```

---

### `test_web_api.py`
**Purpose**: Tests Flask web API endpoints

**What it tests**:
- POST /api/calculate/csv endpoint
- POST /api/calculate/text endpoint
- Parse utilities (/api/parse/currency, /api/parse/date)

**Prerequisites**: Backend server must be running
```bash
cd backend/app/api
python3 server.py
```

**Then run**:
```bash
python3 tests/test_web_api.py
```

---

## Diagnostic Tools

### `diagnostic_calc.py`
**Purpose**: Diagnose specific calculation scenarios

**Use for**:
- Debugging calculation discrepancies
- Verifying specific scenarios
- Manual calculation verification

**Run**:
```bash
python3 tests/diagnostic_calc.py
```

---

### `verify_rate.py`
**Purpose**: Verify interest rate calculations

**What it tests**:
- Simple interest formula
- Compound interest formula
- Day count calculations
- Rate application

**Run**:
```bash
python3 tests/verify_rate.py
```

---

## Running All Tests

To run all tests sequentially:

```bash
cd /Users/camron.haynes/Desktop/SubCloseProd

# Run allocation tests
python3 tests/test_allocation.py
python3 tests/test_allocation_dynamic.py

# Run interest calculation tests
python3 tests/test_late_interest_historical.py
python3 tests/verify_rate.py

# Run programmatic tests
python3 tests/test_programmatic.py

# Run diagnostic
python3 tests/diagnostic_calc.py

# Run API tests (requires backend running)
python3 tests/test_web_api.py
```

---

## Test Data

Tests use realistic scenarios based on:
- Typical venture fund structures
- Multi-close fundraising scenarios
- Industry-standard commitment amounts
- Realistic date ranges

---

## Expected Output

All tests should:
- ✅ Complete without errors
- ✅ Display calculation results
- ✅ Show breakdown by partner/close
- ✅ Verify totals match expectations

If a test fails:
1. Check the error message
2. Verify input data format
3. Review calculation assumptions
4. Use diagnostic_calc.py to debug

---

## Notes

- Tests use the same calculation engine as the web app
- TypeScript engine (`frontend/lib/lateInterestEngine.ts`) has identical logic
- Test scenarios designed to match Excel calculations
- All formulas validated against industry standards
