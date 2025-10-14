#!/usr/bin/env python3
"""
Flask API Server for Late Interest Engine
==========================================
Provides REST API endpoints for the Late Interest Calculator
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import csv
import tempfile
import os
from pathlib import Path
from datetime import date
from decimal import Decimal
from dataclasses import asdict
from io import StringIO

# Add project root to path (where late_interest_engine.py is)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from late_interest_engine import (
    LateInterestEngine,
    parse_natural_currency,
    parse_flexible_date,
    load_from_csv
)
from app.models.data_models import (
    Partner,
    CapitalCall,
    FundAssumptions,
    PrimeRateChange,
    InterestBase,
    InterestCompounding,
    EndDateCalculation
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "Late Interest Engine API"})


@app.route('/api/calculate/csv', methods=['POST'])
def calculate_from_csv():
    """
    Calculate late interest from uploaded CSV file

    Expected CSV format: Same as 'ex late interest tab.csv'
    """
    try:
        # Get CSV file from request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Get optional parameters
        fund_name = request.form.get('fund_name', 'Fund')
        prime_rate = Decimal(request.form.get('prime_rate', '7.5'))
        spread = Decimal(request.form.get('spread', '2.0'))
        compounding = request.form.get('compounding', 'simple')

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            content = file.read().decode('utf-8')
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Load data from CSV
            partners, capital_calls = load_from_csv(temp_path)

            if not partners or not capital_calls:
                return jsonify({"error": "Could not parse CSV. Check format."}), 400

            # Set up assumptions
            assumptions = FundAssumptions(
                fund_name=fund_name,
                late_interest_base=InterestBase.PRIME,
                late_spread=spread,
                prime_rate_history=[
                    PrimeRateChange(effective_date=date(2020, 1, 1), rate=prime_rate)
                ],
                late_interest_compounding=(
                    InterestCompounding.SIMPLE if compounding == 'simple'
                    else InterestCompounding.COMPOUND
                ),
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
                verbose=False
            )

            # Convert to JSON-serializable format
            result = asdict(output)
            return jsonify(result)

        finally:
            # Clean up temp file
            os.unlink(temp_path)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/calculate/text', methods=['POST'])
def calculate_from_text():
    """
    Calculate late interest from natural language text input

    Expected JSON format:
    {
        "fund_name": "Test Fund",
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
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Parse settings
        fund_name = data.get('fund_name', 'Fund')
        prime_rate = Decimal(str(data.get('prime_rate', '7.5')))
        spread = Decimal(str(data.get('spread', '2.0')))
        compounding = data.get('compounding', 'simple')

        # Parse capital calls
        capital_calls = []
        for i, call_data in enumerate(data.get('capital_calls', [])):
            try:
                due_date = parse_flexible_date(call_data['date'])
                percentage = Decimal(str(call_data['percentage']))

                capital_calls.append(CapitalCall(
                    call_number=i + 1,
                    due_date=due_date,
                    call_percentage=percentage
                ))
            except Exception as e:
                return jsonify({
                    "error": f"Error parsing capital call {i+1}: {str(e)}"
                }), 400

        if not capital_calls:
            return jsonify({"error": "No capital calls provided"}), 400

        # Parse partners
        partners = []
        for i, partner_data in enumerate(data.get('partners', [])):
            try:
                name = partner_data['name']
                commitment = parse_natural_currency(partner_data['commitment'])
                close_num = int(partner_data.get('close', 1))

                # Parse issue date if provided, otherwise use first capital call date
                issue_date_str = partner_data.get('issue_date', '')
                if issue_date_str:
                    issue_date = parse_flexible_date(issue_date_str)
                else:
                    issue_date = capital_calls[0].due_date

                partners.append(Partner(
                    name=name,
                    issue_date=issue_date,
                    commitment=commitment,
                    close_number=close_num
                ))
            except Exception as e:
                return jsonify({
                    "error": f"Error parsing partner {i+1}: {str(e)}"
                }), 400

        if not partners:
            return jsonify({"error": "No partners provided"}), 400

        # Set up assumptions
        assumptions = FundAssumptions(
            fund_name=fund_name,
            late_interest_base=InterestBase.PRIME,
            late_spread=spread,
            prime_rate_history=[
                PrimeRateChange(effective_date=date(2020, 1, 1), rate=prime_rate)
            ],
            late_interest_compounding=(
                InterestCompounding.SIMPLE if compounding == 'simple'
                else InterestCompounding.COMPOUND
            ),
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
            verbose=False
        )

        # Convert to JSON-serializable format
        result = asdict(output)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/parse/currency', methods=['POST'])
def parse_currency():
    """
    Parse natural language currency input

    Example: {"value": "10m"} -> {"parsed": 10000000, "formatted": "$10,000,000"}
    """
    try:
        data = request.get_json()
        value = data.get('value', '')

        parsed = parse_natural_currency(value)

        return jsonify({
            "parsed": float(parsed),
            "formatted": f"${parsed:,.2f}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/parse/date', methods=['POST'])
def parse_date():
    """
    Parse flexible date input

    Example: {"value": "1/15/22"} -> {"parsed": "2022-01-15", "formatted": "January 15, 2022"}
    """
    try:
        data = request.get_json()
        value = data.get('value', '')

        parsed = parse_flexible_date(value)

        return jsonify({
            "parsed": str(parsed),
            "formatted": parsed.strftime("%B %d, %Y")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("Late Interest Engine API Server".center(80))
    print("=" * 80)
    print("\nEndpoints:")
    print("  POST /api/calculate/csv   - Calculate from CSV file upload")
    print("  POST /api/calculate/text  - Calculate from JSON input")
    print("  POST /api/parse/currency  - Parse natural language currency")
    print("  POST /api/parse/date      - Parse flexible date format")
    print("  GET  /health              - Health check")
    print("\nStarting server on http://localhost:5000")
    print("=" * 80 + "\n")

    app.run(debug=True, port=5000)
