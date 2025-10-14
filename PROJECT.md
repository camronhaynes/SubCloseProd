# Late Interest Calculator - Project Overview

**A modern web application for calculating late interest on subsequent fund closes**

---

## 🎯 Project Purpose

This application calculates late interest owed by new Limited Partners (LPs) who join a fund after initial capital calls, and allocates that interest pro-rata to existing LPs. The calculation runs entirely in the browser using TypeScript - no Python backend required for calculations.

---

## 📁 Project Structure

```
SubCloseProd/
├── frontend/                    # Next.js web application
│   ├── app/
│   │   └── page.tsx            # Main calculator UI (settings + results)
│   ├── lib/
│   │   └── lateInterestEngine.ts  # TypeScript calculation engine
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
├── backend/                     # Legacy Flask API (optional)
│   ├── app/
│   │   ├── api/
│   │   │   └── server.py       # Flask REST API endpoints
│   │   ├── models/
│   │   │   └── data_models.py  # Python data models
│   │   └── calculators/        # Python calculation modules
│   └── requirements.txt
│
├── tests/                       # Python test scripts
│   ├── test_allocation.py
│   ├── test_allocation_dynamic.py
│   ├── test_late_interest_historical.py
│   ├── test_programmatic.py
│   ├── test_web_api.py
│   ├── diagnostic_calc.py
│   └── verify_rate.py
│
├── late_interest_engine.py      # Core Python calculation engine
├── start_web_app.sh             # Startup script for backend/frontend
├── PROJECT.md                   # This file
└── README.md                    # User documentation

```

---

## 🚀 Quick Start

### Option 1: Frontend Only (Recommended)
The frontend now runs completely standalone with calculations in TypeScript:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Option 2: With Backend (Optional)
If you want to use the Python backend API:

```bash
# Terminal 1 - Backend
cd backend/app/api
python3 server.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## 🏗️ Architecture

### Frontend (Next.js + TypeScript)
- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS
- **Calculation Engine**: Pure TypeScript (`lib/lateInterestEngine.ts`)
- **Key Features**:
  - Runs entirely in browser (no backend needed)
  - CSV import with smart parsing
  - Expandable calculation breakdowns
  - Pro-rata allocation display
  - Sample data demo

### Backend (Flask + Python) - Optional
- **Framework**: Flask with CORS
- **Purpose**: Alternative API interface (not required by frontend)
- **Endpoints**:
  - `POST /api/calculate/csv` - Calculate from CSV upload
  - `POST /api/calculate/text` - Calculate from JSON
  - `POST /api/parse/currency` - Parse currency strings
  - `POST /api/parse/date` - Parse date strings
  - `GET /health` - Health check

---

## 📊 Calculation Logic

### Core Formula

**Simple Interest:**
```
Interest = Principal × Rate × (Days / 365)
```

**Compound Interest:**
```
Amount = Principal × (1 + Rate/n)^(n×t)
Interest = Amount - Principal
```

**Management Fee Allocation:**
```
Time-Weighted Rate = (Days / 365) × Annual Mgmt Fee Rate
Catch-Up Ratio = Catch-Up Capital / LP Commitment
Management Fee = (Time-Weighted Rate / Catch-Up Ratio) × Total Late Interest
```

### Process Flow

1. **Input Collection**
   - Partners with commitments, issue dates, and close numbers
   - Capital calls with due dates and percentages
   - Fund assumptions (rates, compounding, management fees, etc.)

2. **Late Interest Calculation (New LPs)**
   - For each partner joining after Close 1
   - Calculate missed capital calls (catch-up capital)
   - Compute interest from call due date to issue date
   - Apply simple or compound interest based on settings
   - Sum total late interest owed per LP

3. **Management Fee Allocation (Optional)**
   - Calculate time-weighted management fee rate
   - Determine catch-up capital ratio
   - Apply management fee to late interest collected
   - Deduct from total before LP allocation

4. **Pro-Rata Allocation (Existing LPs)**
   - Total late interest collected from new LPs (minus management fees)
   - Allocate to existing LPs based on commitment percentage
   - Support multi-close scenarios with cascading allocations
   - Display breakdown by admitting close

5. **Audit Trail Generation**
   - Create detailed breakdown for each calculation
   - Store intermediate values for verification
   - Generate Excel-compliant formulas for reconciliation

---

## 💾 Data Format

### CSV Import Format
```csv
Name,Issue Date,Commitment,[Close]
ABC Partners,1/1/22,5m,1
New Investor,1/1/25,2m,2
```

**Notes:**
- Commitment supports: `5m`, `5M`, `$5,000,000`, etc.
- Close is optional, defaults to 1
- Handles Carta CSV exports automatically

### Fund Assumptions
- **Interest Base**: Prime rate or flat rate
- **Compounding**: Simple or compound (daily/monthly/quarterly/semi-annual/annual)
- **End Date**: Issue date or due date based
- **Management Fee**: Optional allocation with configurable rate and start date
- **Closes to Date**: Number of existing closes that receive allocations
- **Rounding**: Configurable decimal places for calculations and summations

---

## 🧪 Testing

Test scripts are located in the `tests/` directory:

```bash
# Run allocation tests
python3 tests/test_allocation.py

# Test with historical data
python3 tests/test_late_interest_historical.py

# Verify rate calculations
python3 tests/verify_rate.py

# Test web API (requires backend running)
python3 tests/test_web_api.py
```

---

## 📈 Key Features

### Auditable Calculations
- ✅ **Late Interest Audit**: Click to expand any New LP row
  - See capital call by capital call breakdown
  - View exact formula used: `Capital × Rate% × (Days/365)`
  - Verify days late, rates, and interest per call
  - Color-coded breakdown table with formulas

- ✅ **Management Fee Audit**: Click "audit" button next to management fee
  - Step-by-step calculation breakdown
  - Excel-compliant formula showing all components
  - Displays time-weighted rate and catch-up ratio
  - Shows how management fees are calculated from late interest
  - Color-coded sections for easy verification
  - Full transparency for Excel reconciliation

### Management Fee Allocation
- ✅ Optional management fee calculation on allocated late interest
- ✅ Configurable annual management fee rate
- ✅ Custom management fee start date
- ✅ Excel-compliant formula for accuracy
- ✅ Conditional display (only shows when enabled)
- ✅ Automatically deducted from late interest before LP allocation

### Multi-Close Support
- ✅ Support for unlimited fund closes
- ✅ Cascading allocation (Close 3 pays to Close 1 and 2)
- ✅ Same LP can increase commitment across closes
- ✅ Self-allocation when LP increases commitment
- ✅ Sample data scenarios:
  - Simple 2-close scenario
  - Complex 3-close with cascading
  - Edge case: LP increasing commitment

### Pro-Rata Display
- ✅ Shows each existing LP's percentage share
- ✅ Breaks down allocation by admitting close
- ✅ Handles repeated partners (commitment increases)
- ✅ Visual grouping with indentation for clarity
- ✅ Totals verify to 100%

### Smart CSV Import
- ✅ Auto-detects header rows
- ✅ Handles BOM characters
- ✅ Parses quoted fields (e.g., `"Ned ""Stark"""`
)
- ✅ Supports Carta export format
- ✅ Optional "Close" column (defaults to 1)
- ✅ Natural language support: "5m", "3M", "$5,000,000"

### Sample Data Scenarios
- ✅ "Fill with sample data" - Basic 2-close scenario
- ✅ "Fill with multi-close scenario" - 3-close cascading example
- ✅ "Fill with increased commitment edge case" - LP self-allocation
- ✅ All scenarios demonstrate full calculation flow

### Professional Design
- ✅ Carta design system integration
- ✅ Clean, modern UI with Tailwind CSS
- ✅ Responsive layout for all screen sizes
- ✅ Color-coded sections (blue for LP allocation, green for mgmt fees, orange for late interest)
- ✅ Expandable/collapsible sections for detailed audits
- ✅ Intuitive toggle buttons for audit views

---

## 🔧 Technology Stack

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type-safe calculations
- **Tailwind CSS** - Utility-first styling
- **React Hooks** - State management

### Backend (Optional)
- **Flask** - Python web framework
- **Flask-CORS** - Cross-origin requests
- **Python 3.9+** - Core language

### Calculation Engine
- Pure TypeScript/JavaScript (frontend)
- Pure Python (backend/CLI)
- Identical logic in both implementations

---

## 📝 File Descriptions

### Core Files

| File | Purpose |
|------|---------|
| `frontend/app/page.tsx` | Main UI component with settings and results |
| `frontend/lib/lateInterestEngine.ts` | Complete TypeScript calculation engine |
| `late_interest_engine.py` | Python calculation engine (reference implementation) |
| `backend/app/api/server.py` | Flask REST API server |
| `start_web_app.sh` | Convenient startup script |

### Configuration

| File | Purpose |
|------|---------|
| `frontend/package.json` | Frontend dependencies |
| `frontend/tsconfig.json` | TypeScript configuration |
| `frontend/tailwind.config.ts` | Tailwind CSS configuration |
| `backend/requirements.txt` | Python dependencies |

### Documentation

| File | Purpose |
|------|---------|
| `PROJECT.md` | This file - project overview |
| `README.md` | User-facing documentation |
| `WEB_APP_README.md` | Web application setup guide |
| `USAGE_GUIDE.md` | Detailed usage instructions |
| `QUICK_START.md` | Quick reference guide |

---

## 🎨 UI/UX Design

### Settings Page (Left Column)
- Fund name and basic settings
- Interest rate configuration (prime or flat)
- Compounding settings (simple or compound with frequency)
- End date calculation method
- **Management fee allocation** (optional checkbox)
  - Annual management fee rate
  - Management fee start date
- Closes to date configuration
- Rounding preferences (calculation and summation)

### Data Input (Right Side)
- **Capital Calls Table**
  - Due date and call percentage
  - Add/remove calls dynamically

- **Partners Table**
  - CSV import with auto-detection
  - Manual entry support
  - Color-coded by close (green = existing, orange = new)
  - Close number assignment
  - Natural language commitment parsing

- **Sample Data Buttons**
  - Basic 2-close scenario
  - Multi-close cascading example
  - Increased commitment edge case

### Results Page
- **Summary Statistics**
  - Fund name and calculation date
  - Total late interest collected
  - Total LP allocation
  - Total management fee (when enabled)

- **New LPs Table**: Shows late interest owed
  - Expandable rows with late interest audit
  - Capital call breakdown with formulas
  - Management fee audit button (when enabled)
  - Color-coded totals

- **Existing LPs Table**: Shows pro-rata allocations
  - Percentage share displayed
  - Breakdown by admitting close
  - Visual grouping for repeated partners
  - Commitment increase handling

---

## 🔐 Security Notes

- All calculations run client-side (frontend)
- No sensitive data sent to backend
- CSV files processed in browser memory
- Backend API has CORS enabled for localhost only

---

## 🚧 Future Enhancements

Potential improvements:
- [ ] Export results to Excel/CSV
- [ ] Save/load calculation scenarios
- [ ] Historical prime rate lookup API
- [ ] Multi-currency support
- [ ] Batch processing multiple funds

---

## 📞 Support

For questions or issues:
1. Check the README.md for usage instructions
2. Review USAGE_GUIDE.md for detailed examples
3. Run test scripts in `tests/` to verify calculations

---

## 🏷️ Version

**Current Version**: 2.1
**Last Updated**: October 2025
**Status**: Production Ready

**Major Changes in v2.1:**
- ✅ Added management fee allocation feature with Excel formula compliance
- ✅ Implemented dual audit system (late interest + management fee)
- ✅ Added multi-close support with cascading allocations
- ✅ Enhanced UI with conditional column display
- ✅ Integrated Carta design system
- ✅ Added three sample data scenarios for different use cases

**Major Changes in v2.0:**
- Added TypeScript calculation engine
- Frontend now runs standalone
- Improved CSV import with auto-detection
- Added expandable calculation breakdowns
- Enhanced UI with better data visualization

---

## 📄 License

Internal use only.
