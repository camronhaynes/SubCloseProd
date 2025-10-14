# Complete Example Session

## Scenario
You want to calculate late interest for a fund with:
- **Total Commitments**: $10M from existing LPs
- **New Investor**: $3M joining at subsequent close
- **Capital Calls**: 3 calls at 10%, 15%, and 20%
- **Interest Rate**: Prime (7.5%) + Spread (2.0%) = 9.5%

## Step-by-Step Walkthrough

### 1. Run the command
```bash
python3 late_interest_engine.py --interactive
```

### 2. Interactive Session

```
================================================================================
                  LATE INTEREST ENGINE - INTERACTIVE INPUT MODE                  
================================================================================

Enter fund data interactively. You can use natural language for amounts:
  Examples: '10m', '5M', '2.5m', '500k', '$10,000,000'
  Dates: '1/15/23', 'Jan 15 2023', '2023-01-15'


--------------------------------------------------------------------------------
CAPITAL CALLS
--------------------------------------------------------------------------------
Enter capital call information. Type 'done' when finished.


Capital Call #1:
  Due date (e.g., '1/15/23' or 'done'): 1/15/22
  Call percentage (e.g., '10' for 10%): 10
  ✓ Added Capital Call #1: 2022-01-15, 10%

Capital Call #2:
  Due date (e.g., '1/15/23' or 'done'): 6/15/22
  Call percentage (e.g., '10' for 10%): 15
  ✓ Added Capital Call #2: 2022-06-15, 15%

Capital Call #3:
  Due date (e.g., '1/15/23' or 'done'): 12/15/22
  Call percentage (e.g., '10' for 10%): 20
  ✓ Added Capital Call #3: 2022-12-15, 20%

Capital Call #4:
  Due date (e.g., '1/15/23' or 'done'): done

✓ Total capital calls entered: 3

--------------------------------------------------------------------------------
PARTNERS / LIMITED PARTNERS
--------------------------------------------------------------------------------
Enter partner information. Type 'done' when finished.


Partner #1:
  Partner name (or 'done'): ABC Partners
  Commitment (e.g., '10m', '5M', '500k'): 5m
  Issue date (press Enter for first capital call date): 
  Close number (1 for initial, 2+ for subsequent, default=1): 1
  ✓ Added Partner: ABC Partners, $5,000,000, Close 1

Partner #2:
  Partner name (or 'done'): XYZ Capital
  Commitment (e.g., '10m', '5M', '500k'): 5m
  Issue date (press Enter for first capital call date): 
  Close number (1 for initial, 2+ for subsequent, default=1): 1
  ✓ Added Partner: XYZ Capital, $5,000,000, Close 1

Partner #3:
  Partner name (or 'done'): New Investor LLC
  Commitment (e.g., '10m', '5M', '500k'): 3m
  Issue date (press Enter for first capital call date): 7/1/22
  Close number (1 for initial, 2+ for subsequent, default=1): 2
  ✓ Added Partner: New Investor LLC, $3,000,000, Close 2

Partner #4:
  Partner name (or 'done'): done

✓ Total partners entered: 3

================================================================================
INPUT SUMMARY
================================================================================
Capital Calls: 3
  Call #1: 2022-01-15, 10%
  Call #2: 2022-06-15, 15%
  Call #3: 2022-12-15, 20%

Partners: 3
  ABC Partners: $5,000,000, Close 1
  XYZ Capital: $5,000,000, Close 1
  New Investor LLC: $3,000,000, Close 2

================================================================================

Proceed with calculation? (y/n): y
```

### 3. Calculation Results

```
====================================================================================================
                            LATE INTEREST ENGINE - COMPLETE CALCULATION                             
====================================================================================================

Fund: Fund
Total Partners: 3
Total Capital Calls: 3
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
New Investor LLC          $      3,000,000.00              2 $         15,108.91
----------------------------------------------------------------------------------------------------
TOTAL COLLECTED                                              $         15,108.91

----------------------------------------------------------------------------------------------------
PRO-RATA ALLOCATION TO EXISTING LPs
----------------------------------------------------------------------------------------------------
Partner                   Commitment           % Ownership     Allocation          
----------------------------------------------------------------------------------------------------
ABC Partners              $      5,000,000.00         50.00% $          7,554.46
XYZ Capital               $      5,000,000.00         50.00% $          7,554.46
----------------------------------------------------------------------------------------------------
TOTAL ALLOCATED                                               $         15,108.92

Collected:                     $         15,108.91
Allocated:                     $         15,108.92
Difference:                    $             -0.01
✓ Balanced (within rounding tolerance)

====================================================================================================
FINAL SUMMARY
====================================================================================================
Grand Total Late Interest Collected: $         15,108.91
Grand Total Late Interest Allocated:  $         15,108.92
Difference:                            $             -0.01
====================================================================================================
```

## Explanation of Results

### Late Interest Calculation

**New Investor LLC** joined on 7/1/22 (Close 2) and missed 2 capital calls:

1. **Capital Call #1** (1/15/22):
   - Amount: $3,000,000 × 10% = $300,000
   - Days late: 167 days (from 1/15/22 to 7/1/22)
   - Interest: $300,000 × 9.5% × 167/365 = $13,042.47

2. **Capital Call #2** (6/15/22):
   - Amount: $3,000,000 × 15% = $450,000
   - Days late: 16 days (from 6/15/22 to 7/1/22)
   - Interest: $450,000 × 9.5% × 16/365 = $1,873.97

**Total Late Interest**: $13,042.47 + $1,873.97 = **$14,916.44**

### Pro-Rata Allocation

The $15,108.91 collected is allocated to existing LPs based on ownership:

- **Total existing commitments**: $10,000,000
- **ABC Partners**: $5M / $10M = 50% → $7,554.46
- **XYZ Capital**: $5M / $10M = 50% → $7,554.46

The $0.01 difference is due to rounding, which is within tolerance.

## Save Results to JSON

To save results for further processing:

```bash
python3 late_interest_engine.py --interactive --output-json results.json
```

The JSON output will contain:
- All calculation details
- Breakdown by capital call
- Allocation by partner
- Summary by close
- Fund settings used

## Different Scenarios

### Higher Interest Rate
```bash
python3 late_interest_engine.py --interactive --prime-rate 8.5 --spread 3.0
# Total rate: 11.5%
```

### Compound Interest
```bash
python3 late_interest_engine.py --interactive --compounding compound
```

### Multiple Subsequent Closes
Just add more partners with close numbers 3, 4, etc.:
- Close 1: Original LPs (receive allocations)
- Close 2: First subsequent close (pay interest on missed calls, receive allocations from Close 3)
- Close 3: Second subsequent close (pay interest on all missed calls)
