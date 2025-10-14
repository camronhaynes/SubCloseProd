# Late Interest Calculator - Web Interface

A clean web interface for testing the Late Interest Engine. Upload CSV files or use natural language JSON input to run calculations.

## Features

- **CSV Upload**: Upload your existing CSV files for instant calculations
- **Natural Language Input**: Use friendly formats like "10m", "5M", "500k" for amounts
- **Real-time Results**: See detailed breakdowns of late interest calculations
- **Beautiful UI**: Clean, modern interface built with Next.js and Tailwind CSS

## Quick Start

### 1. Install Backend Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### 2. Start the Flask API Server

```bash
cd backend/app/api
python3 server.py
```

The API will start on `http://localhost:5000`

### 3. Install Frontend Dependencies

In a new terminal:

```bash
cd frontend
npm install
```

### 4. Start the React Frontend

```bash
npm run dev
```

The web app will open at `http://localhost:3000`

## Usage

### CSV Upload Mode

1. Click "CSV Upload" tab
2. Select your CSV file (use the same format as `ex late interest tab.csv`)
3. Configure settings:
   - Fund Name
   - Prime Rate (%)
   - Spread (%)
   - Compounding method
4. Click "Calculate from CSV"

### Natural Language / JSON Mode

1. Click "Natural Language / JSON" tab
2. Enter your scenario in JSON format with natural language amounts:

```json
{
  "fund_name": "Test Fund IV",
  "capital_calls": [
    {"date": "1/15/22", "percentage": "10"},
    {"date": "6/15/22", "percentage": "15"}
  ],
  "partners": [
    {"name": "ABC Partners", "commitment": "5m", "close": 1, "issue_date": "1/15/22"},
    {"name": "New LP", "commitment": "3m", "close": 2, "issue_date": "7/1/22"}
  ],
  "prime_rate": "7.5",
  "spread": "2.0",
  "compounding": "simple"
}
```

3. Click "Calculate from JSON"

## Natural Language Examples

### Currency Amounts:
- `"10m"` → $10,000,000
- `"5M"` → $5,000,000
- `"2.5m"` → $2,500,000
- `"500k"` → $500,000
- `"$1,000,000"` → $1,000,000

### Dates:
- `"1/15/22"` → January 15, 2022
- `"Jan 15 2023"` → January 15, 2023
- `"2023-01-15"` → January 15, 2023

## API Endpoints

The Flask backend provides these endpoints:

- `POST /api/calculate/csv` - Calculate from CSV file upload
- `POST /api/calculate/text` - Calculate from JSON input
- `POST /api/parse/currency` - Test currency parsing
- `POST /api/parse/date` - Test date parsing
- `GET /health` - Health check

## Project Structure

```
SubCloseProd/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── server.py          # Flask API server
│   │   ├── calculators/           # Core calculation logic
│   │   └── models/                # Data models
│   ├── requirements.txt           # Python dependencies
│   └── late_interest_engine.py    # Main engine
├── frontend/
│   ├── app/
│   │   ├── page.tsx              # Main UI component
│   │   ├── layout.tsx            # Layout wrapper
│   │   └── globals.css           # Global styles
│   ├── package.json              # Node dependencies
│   └── tsconfig.json             # TypeScript config
└── WEB_APP_README.md             # This file
```

## Example CSV Format

Your CSV should follow this format (see `ex late interest tab.csv`):

```csv
,Partner,Issue Date,Commitment,Close,Cap Call,1,2,3
,,,,,Due Date,1/15/22,6/15/22,12/15/22
,,,,,Call %,10%,15%,20%
,,,,,,,,
,New LP,7/1/22,"$3,000,000",2,,,,
...
```

## Troubleshooting

### "Error: Connection refused"
- Make sure the Flask server is running on port 5000
- Check that you started `python3 server.py` in the `backend/app/api` directory

### "Could not parse CSV"
- Verify your CSV matches the expected format
- Check that dates and amounts are properly formatted

### "Invalid JSON format"
- Use the JSON validator or copy the example template
- Make sure all strings are in double quotes
- Check for trailing commas

## Development Notes

- The backend uses the same Late Interest Engine as your CLI tools
- All test scripts (`test_*.py`) still work independently
- This web interface is for quick testing and demos
- Results match exactly with your CLI output

## Next Steps

- Add more example scenarios
- Export results as PDF reports
- Save/load calculation scenarios
- Add multi-close visualizations
