'use client'

import { useState } from 'react'
import {
  LateInterestEngine,
  FundAssumptions,
  Partner as EnginePartner,
  CapitalCall as EngineCapitalCall,
  InterestCompounding,
  InterestBase,
  EndDateCalculation,
  parseNaturalCurrency,
  parseFlexibleDate,
} from '../lib/lateInterestEngine'

interface CalculationResult {
  fund_name: string
  calculation_date: string
  total_late_interest_collected: string
  total_late_interest_allocated: string
  total_mgmt_fee_allocation: string
  new_lps: any[]
  existing_lps: any[]
  summary_by_close: any[]
  settings: any
}

interface Partner {
  name: string
  commitment: string
  issue_date: string
  close: string
}

interface CapitalCall {
  date: string
  percentage: string
}

export default function Home() {
  const [isOpen, setIsOpen] = useState(true)
  const [step, setStep] = useState<'settings' | 'results'>('settings')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CalculationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [expandedNewLps, setExpandedNewLps] = useState<Set<number>>(new Set())
  const [expandedMgmtFeeAudits, setExpandedMgmtFeeAudits] = useState<Set<number>>(new Set())

  // Settings state
  const [fundName, setFundName] = useState('Fund')
  const [compounding, setCompounding] = useState('simple')
  const [compoundingFrequency, setCompoundingFrequency] = useState('annually')
  const [interestBase, setInterestBase] = useState('prime')
  const [lateSpread, setLateSpread] = useState('2.0')
  const [primeRate, setPrimeRate] = useState('7.25')
  const [endDate, setEndDate] = useState('issue_date')
  const [catchUpDueDate, setCatchUpDueDate] = useState('')
  const [mgmtFeeEnabled, setMgmtFeeEnabled] = useState(false)
  const [mgmtFeeRate, setMgmtFeeRate] = useState('1.0')
  const [mgmtFeeStartDate, setMgmtFeeStartDate] = useState('')
  const [calcRounding, setCalcRounding] = useState('2')
  const [sumRounding, setSumRounding] = useState('2')
  const [closesToDate, setClosesToDate] = useState('1')

  // Data input state
  const [partnerInput, setPartnerInput] = useState('manual')
  const [partners, setPartners] = useState<Partner[]>([
    { name: '', commitment: '', issue_date: '', close: '1' }
  ])
  const [capitalCalls, setCapitalCalls] = useState<CapitalCall[]>([
    { date: '', percentage: '' }
  ])

  const toggleNewLpExpansion = (idx: number) => {
    const newExpanded = new Set(expandedNewLps)
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx)
    } else {
      newExpanded.add(idx)
    }
    setExpandedNewLps(newExpanded)
  }

  const toggleMgmtFeeAudit = (idx: number) => {
    const newExpanded = new Set(expandedMgmtFeeAudits)
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx)
    } else {
      newExpanded.add(idx)
    }
    setExpandedMgmtFeeAudits(newExpanded)
  }

  const fillSampleData = () => {
    // Sample capital calls
    setCapitalCalls([
      { date: '1/15/22', percentage: '10' },
      { date: '6/15/22', percentage: '20' },
      { date: '12/15/22', percentage: '15' },
    ])

    // Sample partners - mix of existing (Close 1) and new (Close 2)
    setPartners([
      { name: 'ABC Partners', commitment: '5m', issue_date: '1/1/22', close: '1' },
      { name: 'XYZ Capital', commitment: '3m', issue_date: '1/1/22', close: '1' },
      { name: 'Venture Fund LLC', commitment: '2m', issue_date: '1/1/22', close: '1' },
      { name: 'New Investor LP', commitment: '1m', issue_date: '1/1/25', close: '2' },
      { name: 'Late Joiner Partners', commitment: '2.5m', issue_date: '1/1/25', close: '2' },
    ])

    // Set to close 1 as existing
    setClosesToDate('1')
  }

  const fillMultiCloseSampleData = () => {
    // Sample capital calls
    setCapitalCalls([
      { date: '1/15/22', percentage: '10' },
      { date: '6/15/22', percentage: '20' },
      { date: '12/15/22', percentage: '15' },
      { date: '6/15/23', percentage: '10' },
    ])

    // Sample partners - Close 1, 2, and 3 to showcase cascading allocations
    // NOTE: ABC Partners appears in BOTH Close 1 and Close 2 (commitment increase)
    setPartners([
      // Close 1 - Founding investors (receive allocations from Close 2 and 3)
      { name: 'ABC Partners', commitment: '5m', issue_date: '1/1/22', close: '1' },
      { name: 'XYZ Capital', commitment: '3m', issue_date: '1/1/22', close: '1' },
      { name: 'Venture Fund LLC', commitment: '2m', issue_date: '1/1/22', close: '1' },

      // Close 2 - Second close investors (pay interest to Close 1, receive from Close 3)
      // ABC Partners increases commitment (self-allocates interest)
      { name: 'ABC Partners', commitment: '2m', issue_date: '7/1/23', close: '2' },
      { name: 'Growth Equity Fund', commitment: '2m', issue_date: '7/1/23', close: '2' },
      { name: 'Strategic Partners LP', commitment: '1.5m', issue_date: '7/1/23', close: '2' },

      // Close 3 - Third close investors (pay interest to BOTH Close 1 AND Close 2)
      { name: 'Late Stage Capital', commitment: '1.5m', issue_date: '1/1/25', close: '3' },
      { name: 'Final Investor LLC', commitment: '1m', issue_date: '1/1/25', close: '3' },
    ])

    // Set to close 2 as existing, so Close 3 pays interest to both 1 and 2
    setClosesToDate('2')
  }

  const fillIncreasedCommitmentSampleData = () => {
    // Sample capital calls
    setCapitalCalls([
      { date: '1/15/22', percentage: '10' },
      { date: '6/15/22', percentage: '20' },
      { date: '12/15/22', percentage: '15' },
    ])

    // EDGE CASE: LP increases commitment and allocates to themselves
    // Founder LP commits in Close 1, then increases in Close 2
    // Close 2 LPs pay interest to Close 1 (including to themselves!)
    setPartners([
      // Close 1 - Initial commitment
      { name: 'Founder LP (Initial)', commitment: '10m', issue_date: '1/1/22', close: '1' },

      // Close 2 - Same LP increases commitment + other new investors
      // Founder LP PAYS late interest on their increase AND RECEIVES pro-rata allocation
      { name: 'Founder LP (Increase)', commitment: '5m', issue_date: '1/1/24', close: '2' },
      { name: 'New Investor A', commitment: '3m', issue_date: '1/1/24', close: '2' },
      { name: 'New Investor B', commitment: '2m', issue_date: '1/1/24', close: '2' },
    ])

    // Set to close 1 as existing
    // Close 2 investors pay interest to Close 1 (including Founder LP to themselves)
    setClosesToDate('1')
  }

  const addPartner = () => {
    setPartners([...partners, { name: '', commitment: '', issue_date: '', close: '1' }])
  }

  const removePartner = (index: number) => {
    setPartners(partners.filter((_, i) => i !== index))
  }

  const updatePartner = (index: number, field: keyof Partner, value: string) => {
    const updated = [...partners]
    updated[index][field] = value
    setPartners(updated)
  }

  const addCapitalCall = () => {
    setCapitalCalls([...capitalCalls, { date: '', percentage: '' }])
  }

  const removeCapitalCall = (index: number) => {
    setCapitalCalls(capitalCalls.filter((_, i) => i !== index))
  }

  const updateCapitalCall = (index: number, field: keyof CapitalCall, value: string) => {
    const updated = [...capitalCalls]
    updated[index][field] = value
    setCapitalCalls(updated)
  }

  const handlePartnerCSV = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      let text = event.target?.result as string

      // Remove BOM if present
      if (text.charCodeAt(0) === 0xFEFF) {
        text = text.slice(1)
      }

      const lines = text.split('\n')
      const parsedPartners: Partner[] = []

      // Find the header row (contains "Partner" or "Name")
      let headerIndex = -1
      for (let i = 0; i < Math.min(10, lines.length); i++) {
        const line = lines[i].toLowerCase()
        if (line.includes('partner') || line.includes('name')) {
          headerIndex = i
          break
        }
      }

      // Start parsing from row after header
      const startIndex = headerIndex >= 0 ? headerIndex + 1 : 1

      for (let i = startIndex; i < lines.length; i++) {
        const line = lines[i].trim()
        if (!line) continue

        // Handle CSV parsing with quoted fields
        const row = line.match(/(".*?"|[^",]+)(?=\s*,|\s*$)/g)?.map(field =>
          field.replace(/^"(.+)"$/, '$1').trim()
        ) || []

        if (row.length >= 3 && row[0]?.trim()) {
          parsedPartners.push({
            name: row[0].trim(),
            issue_date: row[1]?.trim() || '',
            commitment: row[2]?.trim() || '',
            close: row[3]?.trim() || '1'  // Optional 4th column, defaults to '1'
          })
        }
      }

      if (parsedPartners.length > 0) {
        setPartners(parsedPartners)
      }
    }
    reader.readAsText(file)
  }

  const handleCalculate = async () => {
    setLoading(true)
    setError(null)

    try {
      const validPartners = partners.filter(p => p.name && p.commitment)
      const validCalls = capitalCalls.filter(c => c.date && c.percentage)

      if (validPartners.length === 0) {
        throw new Error('Please add at least one partner')
      }
      if (validCalls.length === 0) {
        throw new Error('Please add at least one capital call')
      }

      // Parse partners
      const parsedPartners: EnginePartner[] = validPartners.map(p => ({
        name: p.name,
        issueDate: parseFlexibleDate(p.issue_date),
        commitment: parseNaturalCurrency(p.commitment),
        closeNumber: parseInt(p.close)
      }))

      // Parse capital calls
      const parsedCalls: EngineCapitalCall[] = validCalls.map((c, idx) => ({
        callNumber: idx + 1,
        dueDate: parseFlexibleDate(c.date),
        callPercentage: parseFloat(c.percentage)
      }))

      // Build assumptions
      const assumptions: FundAssumptions = {
        fundName: fundName,
        lateInterestCompounding: compounding === 'simple'
          ? InterestCompounding.SIMPLE
          : InterestCompounding.COMPOUND,
        lateInterestBase: interestBase === 'prime'
          ? InterestBase.PRIME
          : InterestBase.FLAT,
        lateSpread: parseFloat(lateSpread),
        endDateCalculation: endDate === 'issue_date'
          ? EndDateCalculation.ISSUE_DATE
          : EndDateCalculation.DUE_DATE,
        mgmtFeeAllocatedInterest: mgmtFeeEnabled,
        mgmtFeeRate: mgmtFeeEnabled ? parseFloat(mgmtFeeRate) : undefined,
        mgmtFeeStartDate: mgmtFeeEnabled && mgmtFeeStartDate ? parseFlexibleDate(mgmtFeeStartDate) : undefined,
        calcRounding: parseInt(calcRounding),
        sumRounding: parseInt(sumRounding),
        primeRateHistory: [{
          effectiveDate: new Date(2020, 0, 1),
          rate: parseFloat(primeRate)
        }],
        flatRate: interestBase === 'flat' ? parseFloat(primeRate) : undefined
      }

      // Run calculation
      const engine = new LateInterestEngine(assumptions)
      const output = engine.runCompleteCalculation(
        parsedPartners,
        parsedCalls,
        compoundingFrequency
      )

      // Convert to expected format
      const result: CalculationResult = {
        fund_name: output.fundName,
        calculation_date: output.calculationDate,
        total_late_interest_collected: output.totalLateInterestCollected,
        total_late_interest_allocated: output.totalLateInterestAllocated,
        total_mgmt_fee_allocation: output.totalMgmtFeeAllocation,
        new_lps: output.newLps,
        existing_lps: output.existingLps,
        summary_by_close: output.summaryByClose,
        settings: output.settings
      }

      setResult(result)
      setStep('results')
    } catch (err: any) {
      setError(err.message || 'Calculation failed')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value: string) => {
    const num = parseFloat(value)
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(num)
  }

  const resetAndClose = () => {
    setIsOpen(false)
    setStep('settings')
    setResult(null)
    setError(null)
  }

  return (
    <>
      {/* Calculator Window */}
      {isOpen && (
        <div className="fixed inset-0 bg-gray-100 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-7xl max-h-[95vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="border-b bg-white px-6 py-4 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {step === 'settings' ? 'Configure Late Interest Calculation' : 'Calculation Results'}
                </h2>
                <p className="text-sm text-gray-500">{fundName}</p>
              </div>
              <button
                onClick={resetAndClose}
                className="text-gray-400 hover:text-gray-600 text-2xl font-light px-3"
              >
                ×
              </button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {step === 'settings' ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
                  {/* Left Sidebar - Assumptions */}
                  <div className="lg:col-span-1">
                    <div className="bg-white border border-gray-200 rounded-lg p-6 sticky top-0">
                      <h2 className="text-lg font-bold text-gray-900 mb-4 pb-3 border-b">Assumptions</h2>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Fund Name</label>
                          <input
                            type="text"
                            value={fundName}
                            onChange={(e) => setFundName(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Late Interest Compounding</label>
                          <select
                            value={compounding}
                            onChange={(e) => setCompounding(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-50"
                          >
                            <option value="simple">Simple</option>
                            <option value="compound">Compound</option>
                          </select>
                        </div>

                        {compounding === 'compound' && (
                          <div className="ml-4 pl-4 border-l-2 border-blue-300">
                            <label className="block text-xs font-medium text-gray-600 mb-1">Compounding Frequency</label>
                            <select
                              value={compoundingFrequency}
                              onChange={(e) => setCompoundingFrequency(e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-100"
                            >
                              <option value="daily">Daily (365x)</option>
                              <option value="monthly">Monthly (12x)</option>
                              <option value="quarterly">Quarterly (4x)</option>
                              <option value="semi-annually">Semi-Annually (2x)</option>
                              <option value="annually">Annually (1x)</option>
                            </select>
                            <p className="text-xs text-gray-500 mt-1">How often interest compounds</p>
                          </div>
                        )}

                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Late Interest Base</label>
                          <select
                            value={interestBase}
                            onChange={(e) => setInterestBase(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-50"
                          >
                            <option value="prime">Prime</option>
                            <option value="flat">Flat Rate</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Late Spread (%)</label>
                          <input
                            type="number"
                            step="0.1"
                            value={lateSpread}
                            onChange={(e) => setLateSpread(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-50"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Prime Rate (%) <span className="text-gray-500 text-xs">as of today</span>
                          </label>
                          <input
                            type="number"
                            step="0.01"
                            value={primeRate}
                            onChange={(e) => setPrimeRate(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                          />
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">End Date Calculation</label>
                          <select
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-50"
                          >
                            <option value="issue_date">Issue Date</option>
                            <option value="due_date">Due Date</option>
                          </select>
                        </div>

                        {endDate === 'due_date' && (
                          <div className="ml-4 pl-4 border-l-2 border-blue-300">
                            <label className="block text-xs font-medium text-gray-600 mb-1">Catch-Up Due Date</label>
                            <input
                              type="text"
                              placeholder="1/15/23"
                              value={catchUpDueDate}
                              onChange={(e) => setCatchUpDueDate(e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-100"
                            />
                            <p className="text-xs text-gray-500 mt-1">Due date of catch-up capital call</p>
                          </div>
                        )}

                        <div>
                          <label className="flex items-center space-x-2 mb-2">
                            <input
                              type="checkbox"
                              checked={mgmtFeeEnabled}
                              onChange={(e) => setMgmtFeeEnabled(e.target.checked)}
                              className="rounded border-gray-300"
                            />
                            <span className="text-xs font-medium text-gray-700">Management Fee Allocation</span>
                          </label>
                        </div>

                        {mgmtFeeEnabled && (
                          <div className="ml-4 pl-4 border-l-2 border-blue-300 space-y-3">
                            <div>
                              <label className="block text-xs font-medium text-gray-600 mb-1">Annual Mgmt Fee Rate (%)</label>
                              <input
                                type="number"
                                step="0.1"
                                value={mgmtFeeRate}
                                onChange={(e) => setMgmtFeeRate(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-100"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-medium text-gray-600 mb-1">Mgmt Fee Start Date</label>
                              <input
                                type="text"
                                placeholder="1/1/22"
                                value={mgmtFeeStartDate}
                                onChange={(e) => setMgmtFeeStartDate(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-100"
                              />
                              <p className="text-xs text-gray-500 mt-1">When management fees start accruing</p>
                            </div>
                          </div>
                        )}

                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Closes to Date</label>
                          <input
                            type="number"
                            min="1"
                            max="10"
                            value={closesToDate}
                            onChange={(e) => setClosesToDate(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-50"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Number of existing closes that receive allocations
                          </p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Calc Rounding</label>
                            <input
                              type="number"
                              value={calcRounding}
                              onChange={(e) => setCalcRounding(e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-50"
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">Sum Rounding</label>
                            <input
                              type="number"
                              value={sumRounding}
                              onChange={(e) => setSumRounding(e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-blue-50"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Column - Data Input */}
                  <div className="lg:col-span-2 space-y-6">
                    {/* Capital Calls Section */}
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <div className="flex justify-between items-center mb-4">
                        <h2 className="text-lg font-bold text-gray-900">Capital Calls</h2>
                        <div className="flex flex-col items-end gap-2">
                          <button
                            onClick={fillSampleData}
                            className="text-blue-600 hover:text-blue-800 text-xs font-medium underline"
                          >
                            Fill with sample data to see how it works
                          </button>
                          <button
                            onClick={fillMultiCloseSampleData}
                            className="text-lime-700 hover:text-lime-900 text-xs font-medium underline"
                          >
                            Fill with multi-close scenario
                          </button>
                          <button
                            onClick={fillIncreasedCommitmentSampleData}
                            className="text-green-600 hover:text-green-800 text-xs font-medium underline"
                          >
                            Fill with increased commitment edge case
                          </button>
                          <button
                            onClick={addCapitalCall}
                            className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                          >
                            + Add Call
                          </button>
                        </div>
                      </div>

                      <div className="space-y-3">
                        {capitalCalls.map((call, idx) => (
                          <div key={idx} className="flex gap-3 items-start">
                            <div className="flex-1">
                              <label className="block text-xs text-gray-600 mb-1">Due Date</label>
                              <input
                                type="text"
                                placeholder="1/15/22"
                                value={call.date}
                                onChange={(e) => updateCapitalCall(idx, 'date', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                              />
                            </div>
                            <div className="flex-1">
                              <label className="block text-xs text-gray-600 mb-1">Call %</label>
                              <input
                                type="text"
                                placeholder="10"
                                value={call.percentage}
                                onChange={(e) => updateCapitalCall(idx, 'percentage', e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                              />
                            </div>
                            {capitalCalls.length > 1 && (
                              <button
                                onClick={() => removeCapitalCall(idx)}
                                className="mt-6 px-3 py-2 text-red-600 hover:bg-red-50 rounded text-sm"
                              >
                                Remove
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Partners Section */}
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <div className="flex justify-between items-center mb-4">
                        <h2 className="text-lg font-bold text-gray-900">Partners</h2>
                        <div className="flex gap-2">
                          <label className="px-4 py-2 bg-gray-100 text-gray-700 rounded text-sm cursor-pointer hover:bg-gray-200">
                            Upload CSV
                            <input
                              type="file"
                              accept=".csv"
                              onChange={handlePartnerCSV}
                              className="hidden"
                            />
                          </label>
                          <button
                            onClick={addPartner}
                            className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                          >
                            + Add Partner
                          </button>
                        </div>
                      </div>

                      <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
                        <p className="text-xs text-yellow-800">
                          <strong>Closes 1-{closesToDate}:</strong> Existing LPs (receive allocations)<br />
                          <strong>Close {parseInt(closesToDate) + 1}+:</strong> New LPs (pay late interest)<br />
                          <strong>CSV format:</strong> Name, Issue Date, Commitment, [Close] • Use natural language: "5m", "3M", "500k"<br />
                          <span className="text-xs text-yellow-700">Close column is optional and defaults to 1 if not provided</span>
                        </p>
                      </div>

                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {partners.map((partner, idx) => {
                          const isExisting = parseInt(partner.close) <= parseInt(closesToDate)
                          const bgColor = isExisting ? 'bg-green-50' : 'bg-orange-50'
                          return (
                            <div key={idx} className={`flex gap-3 items-start border-b pb-3 p-2 rounded ${bgColor}`}>
                              <div className="flex-1">
                                <label className="block text-xs text-gray-600 mb-1">Partner Name</label>
                                <input
                                  type="text"
                                  placeholder="ABC Partners"
                                  value={partner.name}
                                  onChange={(e) => updatePartner(idx, 'name', e.target.value)}
                                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                                />
                              </div>
                              <div className="flex-1">
                                <label className="block text-xs text-gray-600 mb-1">Commitment</label>
                                <input
                                  type="text"
                                  placeholder="5m or 5000000"
                                  value={partner.commitment}
                                  onChange={(e) => updatePartner(idx, 'commitment', e.target.value)}
                                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                                />
                              </div>
                              <div className="flex-1">
                                <label className="block text-xs text-gray-600 mb-1">Issue Date</label>
                                <input
                                  type="text"
                                  placeholder="1/15/22"
                                  value={partner.issue_date}
                                  onChange={(e) => updatePartner(idx, 'issue_date', e.target.value)}
                                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                                />
                              </div>
                              <div className="w-20">
                                <label className="block text-xs text-gray-600 mb-1">Close</label>
                                <input
                                  type="text"
                                  placeholder="1"
                                  value={partner.close}
                                  onChange={(e) => updatePartner(idx, 'close', e.target.value)}
                                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                                />
                              </div>
                              {partners.length > 1 && (
                                <button
                                  onClick={() => removePartner(idx)}
                                  className="mt-6 px-3 py-2 text-red-600 hover:bg-red-50 rounded text-sm"
                                >
                                  ×
                                </button>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>

                    {/* Calculate Button */}
                    <button
                      onClick={handleCalculate}
                      disabled={loading}
                      className="w-full bg-green-600 text-white py-4 px-6 rounded-md font-semibold text-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors"
                    >
                      {loading ? 'Calculating...' : 'Calculate Late Interest'}
                    </button>
                  </div>
                </div>
              ) : (
                /* Results View */
                <div className="p-6">
                  <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
                    <div className="grid grid-cols-5 gap-6 mb-6">
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Fund Name</p>
                        <p className="text-sm font-semibold">{result?.fund_name}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Calculation Date</p>
                        <p className="text-sm font-semibold">{result?.calculation_date}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Total Late Interest</p>
                        <p className="text-lg font-bold text-orange-600">
                          {result && formatCurrency(result.total_late_interest_collected)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">LP Allocation</p>
                        <p className="text-lg font-bold text-blue-600">
                          {result && formatCurrency(result.total_late_interest_allocated)}
                        </p>
                      </div>
                      {mgmtFeeEnabled && (
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Mgmt Fee Allocation</p>
                          <p className="text-lg font-bold text-green-600">
                            {result && formatCurrency(result.total_mgmt_fee_allocation)}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* New LPs Table */}
                  {result?.new_lps && result.new_lps.length > 0 && (
                    <div className="bg-white border border-gray-200 rounded-lg mb-4 overflow-hidden">
                      <div className="px-6 py-4 bg-orange-50 border-b">
                        <h3 className="font-semibold text-gray-900">New LPs - Late Calculation</h3>
                        <p className="text-xs text-gray-600 mt-1">Capital call catch-up and late interest due from new investors</p>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="min-w-full">
                          <thead className="bg-gray-50 border-b">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 w-8"></th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Partner</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Issue Date</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Commitment</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Close</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-600">Total Catch-Up</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-600">Total Late Interest</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 bg-blue-50">LP Allocation</th>
                              {mgmtFeeEnabled && (
                                <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 bg-green-50">Mgmt Fee</th>
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            {result.new_lps.map((lp, idx) => {
                              const isExpanded = expandedNewLps.has(idx)
                              return (
                                <>
                                  <tr key={idx} className="border-b hover:bg-gray-50">
                                    <td className="px-4 py-3 text-center">
                                      <button
                                        onClick={() => toggleNewLpExpansion(idx)}
                                        className="text-gray-500 hover:text-gray-700 focus:outline-none"
                                      >
                                        {isExpanded ? '▼' : '▶'}
                                      </button>
                                    </td>
                                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{lp.partner_name}</td>
                                    <td className="px-4 py-3 text-xs text-gray-600">{lp.issue_date}</td>
                                    <td className="px-4 py-3 text-sm text-gray-700">{formatCurrency(lp.commitment)}</td>
                                    <td className="px-4 py-3 text-sm text-gray-600 text-center">{lp.close_number}</td>
                                    <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                                      {formatCurrency(lp.total_catch_up)}
                                    </td>
                                    <td className="px-4 py-3 text-sm text-orange-600 text-right font-semibold">
                                      {formatCurrency(lp.total_late_interest_due)}
                                    </td>
                                    <td className="px-4 py-3 text-sm font-semibold text-blue-700 text-right bg-blue-50">
                                      {formatCurrency(lp.lp_allocation)}
                                    </td>
                                    {mgmtFeeEnabled && (
                                      <td className="px-4 py-3 text-sm font-semibold text-green-700 text-right bg-green-50">
                                        <div className="flex items-center justify-end gap-2">
                                          {formatCurrency(lp.mgmt_fee_allocation)}
                                          {lp.mgmt_fee_audit && parseFloat(lp.mgmt_fee_allocation) > 0 && (
                                            <button
                                              onClick={() => toggleMgmtFeeAudit(idx)}
                                              className="text-xs text-green-600 hover:text-green-800 underline"
                                              title="View management fee calculation"
                                            >
                                              {expandedMgmtFeeAudits.has(idx) ? '▼' : '▶'} audit
                                            </button>
                                          )}
                                        </div>
                                      </td>
                                    )}
                                  </tr>
                                  {isExpanded && (
                                    <tr key={`${idx}-detail`} className="bg-gray-50">
                                      <td colSpan={mgmtFeeEnabled ? 9 : 8} className="px-4 py-4">
                                        <div className="bg-white border border-gray-300 rounded-lg p-4">
                                          <h4 className="text-sm font-semibold text-gray-900 mb-3">
                                            Calculation Breakdown for {lp.partner_name}
                                          </h4>
                                          <div className="overflow-x-auto">
                                            <table className="min-w-full text-xs">
                                              <thead className="bg-gray-100">
                                                <tr>
                                                  <th className="px-3 py-2 text-left font-medium text-gray-600">Call #</th>
                                                  <th className="px-3 py-2 text-left font-medium text-gray-600">Due Date</th>
                                                  <th className="px-3 py-2 text-right font-medium text-gray-600">Call %</th>
                                                  <th className="px-3 py-2 text-right font-medium text-gray-600">Capital Amt</th>
                                                  <th className="px-3 py-2 text-right font-medium text-gray-600">Days Late</th>
                                                  <th className="px-3 py-2 text-right font-medium text-gray-600">Rate %</th>
                                                  <th className="px-3 py-2 text-right font-medium text-gray-600">Interest</th>
                                                  <th className="px-3 py-2 text-left font-medium text-gray-600">Formula</th>
                                                </tr>
                                              </thead>
                                              <tbody>
                                                {lp.breakdown?.map((call: any, callIdx: number) => (
                                                  <tr key={callIdx} className="border-b border-gray-200">
                                                    <td className="px-3 py-2 text-gray-700">{call.call_number}</td>
                                                    <td className="px-3 py-2 text-gray-700">{call.due_date}</td>
                                                    <td className="px-3 py-2 text-right text-gray-700">{call.call_percentage}%</td>
                                                    <td className="px-3 py-2 text-right text-gray-700">{formatCurrency(call.capital_amount)}</td>
                                                    <td className="px-3 py-2 text-right text-gray-700 font-medium">{call.days_late}</td>
                                                    <td className="px-3 py-2 text-right text-gray-700">{call.effective_rate}%</td>
                                                    <td className="px-3 py-2 text-right text-orange-600 font-semibold">
                                                      {formatCurrency(call.late_interest)}
                                                    </td>
                                                    <td className="px-3 py-2 text-gray-600 font-mono text-xs">
                                                      {call.capital_amount} × {call.effective_rate}% × ({call.days_late}/365)
                                                    </td>
                                                  </tr>
                                                ))}
                                              </tbody>
                                              <tfoot className="bg-gray-100 font-semibold">
                                                <tr>
                                                  <td colSpan={6} className="px-3 py-2 text-right text-gray-900">Total:</td>
                                                  <td className="px-3 py-2 text-right text-orange-600">
                                                    {formatCurrency(lp.total_late_interest_due)}
                                                  </td>
                                                  <td></td>
                                                </tr>
                                              </tfoot>
                                            </table>
                                          </div>
                                        </div>
                                      </td>
                                    </tr>
                                  )}
                                  {expandedMgmtFeeAudits.has(idx) && lp.mgmt_fee_audit && mgmtFeeEnabled && (
                                    <tr key={`${idx}-mgmt-audit`} className="bg-green-50">
                                      <td colSpan={9} className="px-4 py-4">
                                        <div className="bg-white border border-green-300 rounded-lg p-4">
                                          <h4 className="text-sm font-semibold text-gray-900 mb-3">
                                            Management Fee Allocation Audit for {lp.partner_name}
                                          </h4>
                                          <div className="space-y-3">
                                            <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                                              <p className="text-xs font-mono text-gray-800">
                                                <strong>Excel Formula:</strong> {lp.mgmt_fee_audit.excel_formula}
                                              </p>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                              <div className="bg-gray-50 p-3 rounded">
                                                <p className="text-xs text-gray-600 mb-1">Management Fee Start Date</p>
                                                <p className="text-sm font-semibold">{lp.mgmt_fee_audit.mgmt_fee_start_date || 'N/A'}</p>
                                              </div>
                                              <div className="bg-gray-50 p-3 rounded">
                                                <p className="text-xs text-gray-600 mb-1">LP Issue Date</p>
                                                <p className="text-sm font-semibold">{lp.mgmt_fee_audit.issue_date}</p>
                                              </div>
                                              <div className="bg-gray-50 p-3 rounded">
                                                <p className="text-xs text-gray-600 mb-1">Days in Period (inclusive)</p>
                                                <p className="text-sm font-semibold">{lp.mgmt_fee_audit.days_in_period} days</p>
                                              </div>
                                              <div className="bg-gray-50 p-3 rounded">
                                                <p className="text-xs text-gray-600 mb-1">Annual Management Fee Rate</p>
                                                <p className="text-sm font-semibold">{lp.mgmt_fee_audit.annual_rate}%</p>
                                              </div>
                                              <div className="bg-blue-50 p-3 rounded border border-blue-200">
                                                <p className="text-xs text-gray-600 mb-1">Catch-Up Capital (D5 in Excel)</p>
                                                <p className="text-sm font-semibold">{formatCurrency(lp.mgmt_fee_audit.catch_up_capital)}</p>
                                              </div>
                                              <div className="bg-blue-50 p-3 rounded border border-blue-200">
                                                <p className="text-xs text-gray-600 mb-1">LP Commitment (G5 in Excel)</p>
                                                <p className="text-sm font-semibold">{formatCurrency(lp.mgmt_fee_audit.commitment)}</p>
                                              </div>
                                              <div className="bg-orange-50 p-3 rounded border border-orange-200">
                                                <p className="text-xs text-gray-600 mb-1">Total Late Interest (SUM(J5:AC5)-G5)</p>
                                                <p className="text-sm font-semibold">{formatCurrency(lp.mgmt_fee_audit.total_late_interest)}</p>
                                              </div>
                                              <div className="bg-purple-50 p-3 rounded border border-purple-200">
                                                <p className="text-xs text-gray-600 mb-1">Catch-Up Ratio</p>
                                                <p className="text-sm font-semibold">{parseFloat(lp.mgmt_fee_audit.catch_up_ratio).toFixed(6)}</p>
                                                <p className="text-xs text-gray-500">{formatCurrency(lp.mgmt_fee_audit.catch_up_capital)} / {formatCurrency(lp.mgmt_fee_audit.commitment)}</p>
                                              </div>
                                            </div>
                                            <div className="bg-green-100 border border-green-300 rounded p-4">
                                              <p className="text-xs text-gray-600 mb-2">Calculation Breakdown:</p>
                                              <p className="text-sm font-mono text-gray-800 mb-2">
                                                Time-Weighted Rate = ({lp.mgmt_fee_audit.days_in_period}/365) × {lp.mgmt_fee_audit.annual_rate}% = {parseFloat(lp.mgmt_fee_audit.time_weighted_rate).toFixed(8)}
                                              </p>
                                              <p className="text-sm font-mono text-gray-800 mb-2">
                                                {lp.mgmt_fee_audit.formula}
                                              </p>
                                              <p className="text-sm font-bold text-green-800">
                                                Management Fee = {formatCurrency(lp.mgmt_fee_audit.calculated_fee)}
                                              </p>
                                            </div>
                                          </div>
                                        </div>
                                      </td>
                                    </tr>
                                  )}
                                </>
                              )
                            })}
                          </tbody>
                          <tfoot className="bg-gray-100 font-semibold">
                            <tr>
                              <td colSpan={5} className="px-4 py-3 text-sm text-gray-900 text-right">Totals:</td>
                              <td className="px-4 py-3 text-sm text-gray-900 text-right">
                                {formatCurrency(result.new_lps.reduce((sum, lp) => sum + parseFloat(lp.total_catch_up), 0).toString())}
                              </td>
                              <td className="px-4 py-3 text-sm text-orange-600 text-right font-bold">
                                {formatCurrency(result.total_late_interest_collected)}
                              </td>
                              <td className="px-4 py-3 text-sm text-blue-700 text-right font-bold bg-blue-50">
                                {formatCurrency(result.total_late_interest_allocated)}
                              </td>
                              {mgmtFeeEnabled && (
                                <td className="px-4 py-3 text-sm text-green-700 text-right font-bold bg-green-50">
                                  {formatCurrency(result.total_mgmt_fee_allocation)}
                                </td>
                              )}
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Existing LPs Table */}
                  {result?.existing_lps && result.existing_lps.length > 0 && (
                    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                      <div className="px-6 py-4 bg-blue-50 border-b">
                        <h3 className="font-semibold text-gray-900">Existing LPs - Pro-Rata Allocation</h3>
                        <p className="text-xs text-gray-600 mt-1">Distribution of late interest collected to existing investors</p>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="min-w-full">
                          <thead className="bg-gray-50 border-b">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Partner</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Commitment</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Close</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-600">Pro-Rata %</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-600 bg-blue-50">Total Allocation</th>
                              {(() => {
                                const allCloses = new Set<string>()
                                result.existing_lps.forEach((lp: any) => {
                                  Object.keys(lp.allocation_by_close || {}).forEach(close => allCloses.add(close))
                                })
                                return Array.from(allCloses).sort((a, b) => parseInt(a) - parseInt(b)).map(close => (
                                  <th key={close} className="px-4 py-3 text-right text-xs font-medium text-gray-600 bg-gray-50">
                                    Close {close}
                                  </th>
                                ))
                              })()}
                            </tr>
                          </thead>
                          <tbody>
                            {(() => {
                              const totalCommitment = result.existing_lps.reduce((sum: number, lp: any) => sum + parseFloat(lp.commitment), 0)
                              const allCloses = new Set<string>()
                              result.existing_lps.forEach((lp: any) => {
                                Object.keys(lp.allocation_by_close || {}).forEach(close => allCloses.add(close))
                              })
                              const sortedCloses = Array.from(allCloses).sort((a, b) => parseInt(a) - parseInt(b))

                              let previousPartnerName = ''
                              return result.existing_lps.map((lp: any, idx: number) => {
                                const proRata = (parseFloat(lp.commitment) / totalCommitment) * 100
                                const isRepeatedPartner = lp.partner_name === previousPartnerName
                                const currentPartnerName = lp.partner_name
                                previousPartnerName = lp.partner_name

                                // Check if next row is same partner for visual grouping
                                const nextLp = result.existing_lps[idx + 1]
                                const hasNextSamePartner = nextLp && nextLp.partner_name === currentPartnerName

                                return (
                                  <tr
                                    key={idx}
                                    className={`border-b hover:bg-gray-50 ${isRepeatedPartner ? 'bg-blue-50/30' : ''}`}
                                  >
                                    <td className={`px-4 py-3 text-sm font-medium text-gray-900 ${isRepeatedPartner ? 'pl-8 text-gray-600' : ''}`}>
                                      {isRepeatedPartner ? (
                                        <span className="italic text-xs">↳ {lp.partner_name}</span>
                                      ) : (
                                        lp.partner_name
                                      )}
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-700">{formatCurrency(lp.commitment)}</td>
                                    <td className="px-4 py-3 text-sm text-gray-600 text-center">
                                      <span className="inline-block px-2 py-0.5 bg-gray-200 rounded text-xs font-medium">
                                        {lp.close_number}
                                      </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-600 text-right">{proRata.toFixed(4)}%</td>
                                    <td className="px-4 py-3 text-sm font-semibold text-blue-700 text-right bg-blue-50">
                                      {formatCurrency(lp.total_allocation)}
                                    </td>
                                    {sortedCloses.map(close => (
                                      <td key={close} className="px-4 py-3 text-sm text-gray-700 text-right bg-gray-50">
                                        {lp.allocation_by_close?.[close] ? formatCurrency(lp.allocation_by_close[close]) : '-'}
                                      </td>
                                    ))}
                                  </tr>
                                )
                              })
                            })()}
                          </tbody>
                          <tfoot className="bg-gray-100 font-semibold">
                            <tr>
                              <td colSpan={3} className="px-4 py-3 text-sm text-gray-900 text-right">Totals:</td>
                              <td className="px-4 py-3 text-sm text-gray-900 text-right">100.0000%</td>
                              <td className="px-4 py-3 text-sm text-blue-700 text-right font-bold bg-blue-50">
                                {formatCurrency(result.total_late_interest_allocated)}
                              </td>
                              {(() => {
                                const allCloses = new Set<string>()
                                result.existing_lps.forEach((lp: any) => {
                                  Object.keys(lp.allocation_by_close || {}).forEach(close => allCloses.add(close))
                                })
                                const sortedCloses = Array.from(allCloses).sort((a, b) => parseInt(a) - parseInt(b))
                                return sortedCloses.map(close => {
                                  const closeTotal = result.existing_lps.reduce((sum: number, lp: any) => {
                                    return sum + (lp.allocation_by_close?.[close] ? parseFloat(lp.allocation_by_close[close]) : 0)
                                  }, 0)
                                  return (
                                    <td key={close} className="px-4 py-3 text-sm text-gray-900 text-right font-bold bg-gray-50">
                                      {formatCurrency(closeTotal.toString())}
                                    </td>
                                  )
                                })
                              })()}
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

          </div>
        </div>
      )}
    </>
  )
}
