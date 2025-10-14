# Late Interest Calculation MVP - Product Specification

## Overview
This document outlines the requirements and business logic for building an MVP web application to calculate late interest for Limited Partners (LPs) admitted to a fund after the initial close. The application replaces a manual Excel-based process with an automated, auditable web-based solution.

## Problem Statement
When new LPs are admitted to a fund at subsequent closes (Close 2, 3, etc.), they must pay "catch-up" contributions for all previous capital calls they missed. Additionally, they owe **late interest** on these catch-up amounts. This late interest is then **allocated pro-rata to existing LPs** who funded the capital calls on time.

Currently, this calculation is performed in Excel templates with complex, difficult-to-audit formulas. The MVP will automate this process in a web application integrated with Carta's capital management platform.

---

## Business Logic & Calculations

### Core Concepts

#### 1. **Capital Calls Structure**
- Each fund has a series of capital calls over time
- Each capital call specifies:
  - **Due Date**: When payment was due
  - **Call Percentage**: % of commitment amount called (e.g., 20%)
  - **Late Interest Rate**: Applicable rate (based on Prime + Spread, or flat rate per LPA)

#### 2. **Late Interest Calculation**
When a new LP joins at a subsequent close, they must pay:

**Formula (Simple Interest):**
```
Late Interest = Capital Called Amount × Annual Interest Rate × (Days Late / 365)
```

Where:
- **Capital Called Amount** = LP Commitment × Call %
- **Days Late** = Days between Capital Call Due Date and LP Issue Date (or Due Date, depending on LPA terms)
- **Annual Interest Rate** = Effective rate (Prime + Spread, or flat rate)

**Example:**
- New LP commitment: $5,000,000
- Cap Call 1: 20% called on 4/20/22
- New LP Issue Date: 10/31/25
- Days Late: ~1,290 days (3.53 years)
- Late Interest Rate: 9.25% (Prime 7.25% + 2% spread)
- Capital Called: $1,000,000
- **Late Interest = $1,000,000 × 9.25% × (1290/365) = ~$336,014**

#### 3. **Variable Interest Rates (Prime-Based)**
If LPA specifies Prime-based rates:
- Historical prime rate changes must be applied chronologically
- Calculate interest in **segments** for each prime rate period
- Example: If prime was 5.5% from 4/20/22-7/28/22, then 6.25% from 7/28/22-9/22/22, calculate separately and sum

#### 4. **Pro-Rata Allocation to Existing LPs**
All late interest collected from new LPs is **distributed to existing LPs** based on their commitment amounts.

**Allocation Formula:**
```
LP Allocation = (LP Commitment / Total Existing Commitments) × Total Late Interest
```

**Example:**
- Total Late Interest from Close 2: $704,223.29
- Existing LP commitment: $250,000
- Total existing commitments: $23,766,226.58
- **LP Allocation = ($250,000 / $23,766,226.58) × $704,223.29 = $7,406.64**

#### 5. **Multi-Close Scenarios**
Critical nuance: An LP admitted at Close 2 becomes an "existing LP" for Close 3 purposes.

**Example:**
- **Close 1**: Original LPs (pay no late interest)
- **Close 2**: New LP joins
  - Pays late interest to Close 1 LPs
  - Does NOT receive allocation from their own late interest
- **Close 3**: Another new LP joins
  - Pays late interest to Close 1 AND Close 2 LPs (including the Close 2 LP)
  - Close 2 LP now receives pro-rata allocation from Close 3

#### 6. **Commitment Increases**
If an existing LP increases their commitment at a subsequent close:
- The **increased amount** is treated as a new late-arriving commitment
- The LP pays late interest on the increased portion
- The LP simultaneously receives pro-rata allocation from their own late interest (based on their pre-increase commitment)

**Example:**
- LP had $1M commitment at Close 1
- LP increases to $2M at Close 3
- LP pays late interest on $1M increase
- LP receives allocation from their own late interest based on original $1M pro-rata share

---

## Configuration Parameters

### Assumptions (Fund-Level Settings)

| Parameter | Options | Description |
|-----------|---------|-------------|
| **Late Interest Compounding** | Simple / Compound | MVP: Simple only |
| **Late Interest Base** | Prime / Flat Rate | Prime = variable rate based on historical data; Flat = fixed % |
| **Late Spread** | Percentage (e.g., 2%) | Added to base rate (e.g., Prime + 2%) |
| **Prime Rate Date** | Today / Historical | Whether to use current prime or historical lookback |
| **End Date Calculation** | Issue Date / Due Date | Calculate late interest through admission date OR just to capital call due date |
| **Mgmt Fee Allocated Interest** | Yes / No | Whether management fees owe/receive late interest (MVP: No) |
| **Allocated to all Existing LPs** | Yes / No | Whether to distribute to all existing LPs or subset |
| **Calc Rounding** | Decimal places (e.g., 2) | Rounding for intermediate calculations |
| **Sum Rounding** | Decimal places (e.g., 2) | Rounding for final totals |

### Historical Prime Rates
Must maintain a table of historical prime rate changes:
```
Date       | Rate
-----------|------
9/17/25    | 7.25%
12/19/24   | 7.50%
11/8/24    | 7.75%
9/19/24    | 8.00%
...
```

---

## Data Models

### Input Data Required

#### 1. Fund Configuration
- Fund name/ID
- Assumption settings (from table above)
- Historical prime rate table

#### 2. Existing Partners List
```
{
  partner_name: string
  issue_date: date
  commitment: decimal
  close_number: integer
}
```

#### 3. Capital Calls
```
{
  call_number: integer
  due_date: date
  call_percentage: decimal (0-100)
  late_rate: decimal (if flat rate, otherwise calculated from Prime)
}
```

#### 4. New LP Information
```
{
  partner_name: string
  issue_date: date (admission date)
  commitment: decimal
  close_number: integer
}
```

### Output Data

#### 1. New LP Late Interest Summary
```
{
  partner_name: string
  total_catch_up: decimal
  total_late_interest_due: decimal
  breakdown_by_capital_call: [
    {
      call_number: integer
      due_date: date
      call_percentage: decimal
      capital_amount: decimal
      late_interest: decimal
      days_late: integer
      effective_rate: decimal
    }
  ]
}
```

#### 2. Existing LP Allocation Summary
```
{
  partner_name: string
  commitment: decimal
  close_number: integer
  total_allocation: decimal
  allocation_by_close: {
    close_2: decimal
    close_3: decimal
    ...
  }
}
```

---

## MVP Scope

### Phase 1: Core Calculation Engine
**In Scope:**
- Simple interest calculation (not compound)
- Prime-based rates with historical rate periods
- Flat rate calculation
- Issue Date vs Due Date toggle
- Pro-rata allocation to existing LPs
- Multi-close support (Close 2, 3, 4, etc.)
- Export results to CSV

**Out of Scope (Future):**
- Compound interest
- Management fee late interest allocation
- Commitment increase scenarios
- Integration with Carta API for automatic data pull
- Automated email notifications
- Multi-currency support

### Phase 2: Web Interface
**Features:**
- Upload capital calls (CSV or manual entry)
- Upload existing partners list (CSV or manual entry)
- Configure fund assumptions
- Add new LP details
- Display calculation results in table format
- Export results to CSV/Excel

### Phase 3: Integration (Future)
- Carta API integration for partner/capital call data
- Database persistence
- Multi-fund support
- User authentication
- Audit trail

---

## User Flow (MVP)

1. **Setup Fund Configuration**
   - Enter fund name
   - Set calculation assumptions (Prime/Flat, End Date, etc.)
   - Upload historical prime rates (if Prime-based)

2. **Import Existing Data**
   - Upload existing partners list (CSV)
   - Upload capital calls history (CSV)

3. **Add New LP**
   - Enter new LP details (name, commitment, issue date, close number)
   - Submit calculation

4. **Review Results**
   - View new LP late interest breakdown by capital call
   - View existing LP allocation table
   - Download results as CSV

5. **Iterate** (if multiple new LPs)
   - Add additional new LPs
   - System automatically handles multi-close scenarios

---

## Technical Considerations

### Calculation Accuracy
- Use **Decimal** types (not float) for all monetary calculations
- Apply rounding only at specified steps per Calc/Sum Rounding settings
- Validate that allocated amounts sum to total collected late interest

### Date Handling
- Store all dates in ISO 8601 format
- Handle leap years correctly in day counting (365-day year basis standard)
- Timezone: Use fund's local timezone consistently

### Performance
- For MVP, optimize for accuracy over speed
- Support up to 100 capital calls
- Support up to 1,000 existing LPs

### Validation
- Commitment amounts must be positive
- Capital call percentages must sum to ≤100%
- Issue dates must be after fund inception
- Close numbers must be sequential

---

## Open Questions / Future Enhancements

1. **How to handle management fees in late interest calculations?**
   - MVP: Exclude management fees
   - Future: Add toggle and logic

2. **What if an LP is admitted mid-capital-call-period?**
   - If cap call due date is after their admission, do they owe late interest?
   - MVP assumption: Only calculate for cap calls before admission

3. **Audit trail requirements?**
   - Future: Log all calculations with inputs/outputs for compliance

4. **What if historical prime rate data is incomplete?**
   - MVP: Require complete data upload
   - Future: API integration with Fed data

5. **How to handle commitment decreases or withdrawals?**
   - Out of scope for MVP

---

## Success Metrics

**MVP Success Criteria:**
- Accurately replicates Excel template calculations within $0.01
- Reduces calculation time from 2+ hours to <5 minutes
- Eliminates manual formula errors
- Generates auditable output reports

**User Acceptance:**
- Fund administrators can complete late interest calculations without Excel
- Results can be exported and imported into Carta
- Calculations can be explained/audited by third parties

---

## Next Steps

1. Review and approve specification
2. Design database schema and API contracts
3. Build backend calculation engine with unit tests
4. Build frontend UI mockups for approval
5. Implement MVP features
6. User acceptance testing with real fund data
7. Deploy to staging environment
8. Production deployment
