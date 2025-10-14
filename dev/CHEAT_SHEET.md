# Late Interest Engine - Cheat Sheet

## 🎯 Most Common Commands

### 1. Basic Run (See Everything)
```bash
python3 late_interest_engine.py --csv "ex late interest tab.csv"
```
**Use this when:** You want to review all calculations on screen

---

### 2. Export to JSON
```bash
python3 late_interest_engine.py --csv "ex late interest tab.csv" --output-json results.json
```
**Use this when:** You need structured data for Excel/database/reports

---

### 3. Custom Rate
```bash
python3 late_interest_engine.py --csv "ex late interest tab.csv" --prime-rate 8.0 --spread 2.5
```
**Use this when:** Prime rate changed or modeling scenarios

---

### 4. Quiet Mode
```bash
python3 late_interest_engine.py --csv "ex late interest tab.csv" --output-json results.json --quiet
```
**Use this when:** Running in scripts, only want file output

---

### 5. Named Fund
```bash
python3 late_interest_engine.py --csv "ex late interest tab.csv" --fund-name "My Fund LP"
```
**Use this when:** You want proper labeling in output

---

## 📊 What You Get

### Console Output Shows:
- ✅ Late interest per new LP
- ✅ Pro-rata allocation per existing LP
- ✅ Ownership percentages
- ✅ Balance verification
- ✅ Summary totals

### JSON Output Contains:
- Fund name & calculation date
- Total collected & allocated
- New LP details with per-call breakdown
- Existing LP allocations by close
- All settings used

---

## 🔢 The Math (Simple!)

### Late Interest Per Capital Call:
```
Interest = Capital × (Rate/100) × ((End Date - Due Date + 1) / 365)
```

**Example:**
- Capital: $1,000,000
- Rate: 9.5%
- Days: 1,290
- Interest: $1,000,000 × 0.095 × (1290/365) = **$336,013.70**

### Pro-Rata Allocation:
```
Allocation = Total Late Interest × (LP Commitment / Total Existing Commitments)
```

**Example:**
- Total Interest: $704,223.29
- Partner A: $1M / $23.75M = 4.21%
- Allocation: $704,223.29 × 4.21% = **$29,626.56**

---

## 🎛️ Settings Quick Reference

| Setting | What It Changes | Typical Value |
|---------|----------------|---------------|
| `--prime-rate` | Base interest rate | `7.5` |
| `--spread` | Added to prime | `2.0` |
| `--compounding` | Interest method | `simple` |
| `--calc-rounding` | Decimal places | `2` |

**Total Rate = Prime + Spread**
- Example: 7.5% + 2.0% = **9.5%**

---

## ⚡ Power User Commands

### Save with Timestamp:
```bash
python3 late_interest_engine.py --csv "data.csv" --output-json "calc_$(date +%Y%m%d).json"
```

### Multiple Scenarios:
```bash
# Low rate scenario
python3 late_interest_engine.py --csv "data.csv" --prime-rate 7.0 --output-json low.json --quiet

# Base rate scenario  
python3 late_interest_engine.py --csv "data.csv" --prime-rate 7.5 --output-json base.json --quiet

# High rate scenario
python3 late_interest_engine.py --csv "data.csv" --prime-rate 8.0 --output-json high.json --quiet
```

### Find Specific Partner:
```bash
python3 late_interest_engine.py --csv "data.csv" | grep "Partner 21"
```

### Save Report to File:
```bash
python3 late_interest_engine.py --csv "data.csv" > report_$(date +%Y%m%d).txt
```

---

## 🐛 Quick Fixes

**CSV not loading?**
→ Check file path, use quotes: `--csv "my folder/file.csv"`

**Wrong numbers?**
→ Check rate: `--prime-rate 7.5 --spread 2.0`

**Need help?**
→ Run: `python3 late_interest_engine.py --help`

---

## 📋 Your CSV Must Have:

1. **Capital calls** (rows 1-3):
   - Row 1: Call numbers
   - Row 2: Due dates
   - Row 3: Percentages

2. **New LPs** (row 5+):
   - Partner name, issue date, commitment, close number

3. **Existing LPs** (row 19+):
   - Partner name, issue date, commitment, close number

**You already have this format!** → `ex late interest tab.csv`

---

## 🎯 Real-World Example

**Scenario:** Calculate for Close 2, save to JSON for records

```bash
python3 late_interest_engine.py \
  --csv "ex late interest tab.csv" \
  --fund-name "Acme Capital Fund II" \
  --prime-rate 7.5 \
  --spread 2.0 \
  --output-json "close2_$(date +%Y%m%d).json"
```

**Result:**
- ✅ Calculates late interest at 9.5% (7.5% + 2%)
- ✅ Shows all allocations on screen
- ✅ Saves to `close2_20251013.json`
- ✅ Ready for audit/records

---

**That's it! Keep this handy for quick reference.** 📌
