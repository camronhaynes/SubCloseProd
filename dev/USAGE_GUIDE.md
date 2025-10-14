# Late Interest Engine - Usage Guide

## 🚀 Quick Start (3 Simple Steps)

### **Step 1: Prepare Your CSV File**

Your CSV should have:
- Capital calls with due dates and percentages (in header rows)
- Existing LPs with commitments and close numbers
- New LPs joining at subsequent closes

**You already have this!** → `ex late interest tab.csv`

---

### **Step 2: Run the Engine**

```bash
python3 late_interest_engine.py --csv "ex late interest tab.csv"
```

That's it! You'll see:
- ✅ Late interest calculations for new LPs
- ✅ Pro-rata allocations to existing LPs
- ✅ Detailed breakdowns by capital call
- ✅ Summary with totals

---

### **Step 3: Get Results**

The engine shows you:

```
====================================================================
LATE INTEREST DUE FROM NEW LPs
====================================================================
Partner                   Commitment           Late Interest
--------------------------------------------------------------------
New LP                    $5,000,000.00        $704,223.29
--------------------------------------------------------------------

====================================================================
PRO-RATA ALLOCATION TO EXISTING LPs
====================================================================
Partner                   Commitment           Allocation
--------------------------------------------------------------------
Partner 1                 $250,000.00          $7,406.64
Partner 2                 $500,000.00          $14,813.28
...
```

---

## 📊 Common Use Cases

### **Use Case 1: Standard Calculation**

**Scenario:** Calculate late interest for Close 2 with current prime rate

```bash
python3 late_interest_engine.py --csv "ex late interest tab.csv"
```

**Output:**
- Console display with all calculations
- Shows each partner's allocation
- Verifies balanced totals

---

### **Use Case 2: Export to JSON**

**Scenario:** Need data for Excel, database, or API integration

```bash
python3 late_interest_engine.py \
  --csv "ex late interest tab.csv" \
  --output-json results.json
```

**Result:** Creates `results.json` with structured data:

```json
{
  "fund_name": "Fund",
  "total_late_interest_collected": "704223.29",
  "total_late_interest_allocated": "704223.33",
  "new_lps": [ ... ],
  "existing_lps": [ ... ]
}
```

**Use the JSON to:**
- Import into Excel (Power Query)
- Store in database
- Send to APIs
- Generate reports

---

### **Use Case 3: Different Interest Rate**

**Scenario:** Prime rate changed or you want to model different scenarios

```bash
python3 late_interest_engine.py \
  --csv "ex late interest tab.csv" \
  --prime-rate 8.0 \
  --spread 2.5
```

**Result:** Calculates with 10.5% total rate (8.0% + 2.5%)

---

### **Use Case 4: Quiet Mode (No Console Output)**

**Scenario:** Running in scripts, only want JSON output

```bash
python3 late_interest_engine.py \
  --csv "ex late interest tab.csv" \
  --output-json results.json \
  --quiet
```

**Result:** No console output, only creates JSON file

---

### **Use Case 5: Custom Fund Name**

**Scenario:** Want to label output with specific fund name

```bash
python3 late_interest_engine.py \
  --csv "ex late interest tab.csv" \
  --fund-name "Acme Capital Fund II"
```

**Result:** Output shows "Acme Capital Fund II" everywhere

---

## 🎛️ All Available Options

| Option | What It Does | Example | Default |
|--------|--------------|---------|---------|
| `--csv` | Path to your CSV file | `--csv "data.csv"` | **Required** |
| `--fund-name` | Name of the fund | `--fund-name "My Fund"` | `"Fund"` |
| `--prime-rate` | Prime rate % | `--prime-rate 8.0` | `7.5` |
| `--spread` | Spread added to prime | `--spread 2.5` | `2.0` |
| `--compounding` | Interest method | `--compounding simple` | `simple` |
| `--end-date-calc` | End date method | `--end-date-calc issue_date` | `issue_date` |
| `--calc-rounding` | Intermediate rounding | `--calc-rounding 4` | `2` |
| `--sum-rounding` | Final sum rounding | `--sum-rounding 2` | `2` |
| `--output-json` | Save JSON file | `--output-json out.json` | None |
| `--quiet` | Suppress console output | `--quiet` | Show output |

---

## 📖 Understanding the Output

### **Section 1: Fund Summary**

```
Fund: Demo Fund
Total Partners: 53
Total Capital Calls: 6
Closes: [1, 2]
Interest Rate: Prime 7.5% + Spread 2.0% = 9.5%
```

**What it means:**
- 53 partners loaded from CSV
- 6 capital calls detected
- Processing Close 2 (Close 1 doesn't have late interest)
- Using 9.5% interest rate

---

### **Section 2: Late Interest Calculations**

```
Partner                   Commitment           Missed Calls    Late Interest
New LP                    $5,000,000.00        6               $704,223.29
```

**What it means:**
- New LP has $5M commitment
- Missed 6 capital calls before joining
- Owes $704,223.29 in late interest

**Per-Call Breakdown:**
The JSON output shows details for each capital call:
```json
{
  "call_number": 1,
  "due_date": "2022-04-20",
  "capital_amount": "1000000.00",
  "late_interest": "336013.70",
  "days_late": 1290,
  "effective_rate": "9.50"
}
```

---

### **Section 3: Pro-Rata Allocation**

```
Partner                   Commitment           % Ownership     Allocation
Partner 1                 $250,000.00          1.05%          $7,406.64
Partner 21                $3,000,000.00        12.62%         $88,879.67
```

**How it works:**
1. **Calculate ownership %**: Partner's commitment ÷ Total existing commitments
2. **Allocate proportionally**: Late interest × Ownership %

**Example for Partner 21:**
- Commitment: $3,000,000
- Total existing: $23,750,000
- Ownership: 12.62% ($3M ÷ $23.75M)
- Allocation: $704,223.29 × 12.62% = **$88,879.67**

---

### **Section 4: Balance Check**

```
Collected:   $704,223.29
Allocated:   $704,223.33
Difference:  $-0.04
✓ Balanced (within rounding tolerance)
```

**What it means:**
- New LP paid: $704,223.29
- Existing LPs received: $704,223.33
- Difference of $0.04 is from rounding (normal and acceptable)

---

## 💡 Pro Tips

### **Tip 1: Save Your JSON Output**

Always save JSON for records and auditing:

```bash
python3 late_interest_engine.py \
  --csv "ex late interest tab.csv" \
  --output-json "close_2_calculations_$(date +%Y%m%d).json"
```

This creates: `close_2_calculations_20251013.json`

---

### **Tip 2: Compare Different Rates**

Model different scenarios by running multiple times:

```bash
# Scenario 1: Current rate
python3 late_interest_engine.py --csv "data.csv" --prime-rate 7.5 --output-json scenario1.json --quiet

# Scenario 2: Higher rate
python3 late_interest_engine.py --csv "data.csv" --prime-rate 8.0 --output-json scenario2.json --quiet

# Scenario 3: Lower rate
python3 late_interest_engine.py --csv "data.csv" --prime-rate 7.0 --output-json scenario3.json --quiet
```

Then compare the JSON files!

---

### **Tip 3: Pipe to File**

Save the console output to a text file:

```bash
python3 late_interest_engine.py --csv "ex late interest tab.csv" > calculation_report.txt
```

Now you have a permanent text record.

---

### **Tip 4: Check Specific Partner**

Use grep to find a specific partner's allocation:

```bash
python3 late_interest_engine.py --csv "ex late interest tab.csv" | grep "Partner 21"
```

Output: `Partner 21    $3,000,000.00    12.62%    $88,879.67`

---

## 🔍 Troubleshooting

### **Problem: "CSV file not found"**

**Solution:** Check the file path. Use quotes if path has spaces:

```bash
python3 late_interest_engine.py --csv "my files/data.csv"
```

---

### **Problem: "Could not load data from CSV"**

**Solution:** Verify CSV format. Check that:
- Row 1-3: Capital call headers
- Row 5+: New LP data (optional)
- Row 19+: Existing LP data

---

### **Problem: Numbers don't match expected**

**Solution:** Check these settings:
- Prime rate (`--prime-rate`)
- Spread (`--spread`)
- Compounding method (`--compounding`)
- Rounding settings (`--calc-rounding`, `--sum-rounding`)

---

### **Problem: "Module not found"**

**Solution:** Make sure you're in the correct directory:

```bash
cd /Users/camron.haynes/Desktop/SubCloseProd
python3 late_interest_engine.py --csv "ex late interest tab.csv"
```

---

## 📚 Next Steps

1. **Test with your data:** Run the engine with your CSV
2. **Review results:** Check allocations make sense
3. **Export JSON:** Save for integration with other systems
4. **Automate:** Add to your workflow/scripts

---

## 🎓 Example Session

Here's a complete example session:

```bash
# Navigate to project folder
cd /Users/camron.haynes/Desktop/SubCloseProd

# Run basic calculation
python3 late_interest_engine.py --csv "ex late interest tab.csv"

# Save results to JSON
python3 late_interest_engine.py \
  --csv "ex late interest tab.csv" \
  --fund-name "Demo Fund" \
  --output-json demo_results.json

# View JSON
cat demo_results.json | python3 -m json.tool | less

# Find Partner 21's allocation
cat demo_results.json | python3 -m json.tool | grep -A 5 "Partner 21"
```

---

## 📞 Help

- **Full docs:** See `README.md`
- **Quick reference:** See `QUICK_START.md`
- **All options:** Run `python3 late_interest_engine.py --help`

---

**You're all set! Start calculating! 🚀**
