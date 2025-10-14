/**
 * Late Interest Engine - TypeScript Implementation
 * Complete calculation engine for late interest on subsequent fund closes
 * Runs entirely in the browser - no backend needed
 */

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export enum InterestCompounding {
  SIMPLE = 'simple',
  COMPOUND = 'compound',
}

export enum InterestBase {
  PRIME = 'prime',
  FLAT = 'flat',
}

export enum EndDateCalculation {
  ISSUE_DATE = 'issue_date',
  DUE_DATE = 'due_date',
}

export interface PrimeRateChange {
  effectiveDate: Date
  rate: number // As percentage, e.g., 7.25 for 7.25%
}

export interface FundAssumptions {
  fundName: string
  lateInterestCompounding: InterestCompounding
  lateInterestBase: InterestBase
  lateSpread: number // Percentage added to base rate
  endDateCalculation: EndDateCalculation
  mgmtFeeAllocatedInterest: boolean
  mgmtFeeRate?: number // Annual management fee rate (as percentage)
  mgmtFeeStartDate?: Date // When management fees start accruing
  calcRounding: number
  sumRounding: number
  primeRateHistory: PrimeRateChange[]
  flatRate?: number
}

export interface Partner {
  name: string
  issueDate: Date
  commitment: number
  closeNumber: number
}

export interface CapitalCall {
  callNumber: number
  dueDate: Date
  callPercentage: number // As percentage, e.g., 20 for 20%
}

export interface LateInterestDetail {
  callNumber: number
  dueDate: Date
  callPercentage: number
  capitalAmount: number
  lateInterest: number
  daysLate: number
  effectiveRate: number
}

export interface MgmtFeeAudit {
  mgmtFeeStartDate: Date | undefined
  issueDate: Date
  daysInPeriod: number
  annualRate: number
  catchUpCapital: number
  totalLateInterest: number
  commitment: number
  timeWeightedRate: number
  catchUpRatio: number
  calculatedFee: number
  formula: string
  excelFormula: string
}

export interface NewLPCalculation {
  partnerName: string
  issueDate: Date
  commitment: number
  closeNumber: number
  totalCatchUp: number
  totalLateInterestDue: number
  mgmtFeeAllocation: number
  lpAllocation: number
  breakdownByCapitalCall: LateInterestDetail[]
  mgmtFeeAudit?: MgmtFeeAudit
}

export interface ExistingLPAllocation {
  partnerName: string
  commitment: number
  closeNumber: number
  totalAllocation: number
  allocationByAdmittingClose: Record<number, number>
}

export interface EngineOutput {
  fundName: string
  calculationDate: string
  totalLateInterestCollected: string
  totalLateInterestAllocated: string
  totalMgmtFeeAllocation: string
  newLps: any[]
  existingLps: any[]
  summaryByClose: any[]
  settings: any
}

// ============================================================================
// UTILITIES
// ============================================================================

function roundAmount(amount: number, decimalPlaces: number): number {
  if (decimalPlaces === 0) {
    return Math.round(amount)
  }
  const multiplier = Math.pow(10, decimalPlaces)
  return Math.round(amount * multiplier) / multiplier
}

function daysBetween(startDate: Date, endDate: Date): number {
  const msPerDay = 1000 * 60 * 60 * 24
  return Math.floor((endDate.getTime() - startDate.getTime()) / msPerDay)
}

// ============================================================================
// INTEREST RATE CALCULATOR
// ============================================================================

class InterestRateCalculator {
  private compounding: InterestCompounding
  private isFlatRate: boolean
  private flatRate: number
  private rateHistory: PrimeRateChange[]
  private spread: number

  constructor(
    compounding: InterestCompounding,
    rateHistory?: PrimeRateChange[],
    spread?: number,
    flatRate?: number
  ) {
    this.compounding = compounding

    if (flatRate !== undefined) {
      this.isFlatRate = true
      this.flatRate = flatRate
      this.rateHistory = []
      this.spread = 0
    } else if (rateHistory) {
      this.isFlatRate = false
      this.rateHistory = [...rateHistory].sort(
        (a, b) => b.effectiveDate.getTime() - a.effectiveDate.getTime()
      )
      this.spread = spread || 0
      this.flatRate = 0
    } else {
      throw new Error('Must provide either rateHistory or flatRate')
    }
  }

  getRateAtDate(targetDate: Date): number {
    if (this.isFlatRate) {
      return this.flatRate
    }

    for (const rateChange of this.rateHistory) {
      if (targetDate >= rateChange.effectiveDate) {
        return rateChange.rate + this.spread
      }
    }

    if (this.rateHistory.length > 0) {
      return this.rateHistory[this.rateHistory.length - 1].rate + this.spread
    }

    throw new Error('No rate history available')
  }

  private calculateSimpleInterest(
    principal: number,
    startDate: Date,
    endDate: Date
  ): [number, number] {
    // Add +1 for inclusive day counting (Excel convention)
    const totalDays = daysBetween(startDate, endDate) + 1
    if (totalDays <= 0) {
      return [0, 0]
    }

    if (this.isFlatRate) {
      const rate = this.flatRate
      const interest = principal * (rate / 100) * (totalDays / 365)
      return [interest, rate]
    }

    // Variable rate: segment by rate changes
    let totalInterest = 0
    const rateChangesInPeriod = this.rateHistory.filter(
      (rc) => startDate < rc.effectiveDate && rc.effectiveDate <= endDate
    )
    rateChangesInPeriod.sort(
      (a, b) => a.effectiveDate.getTime() - b.effectiveDate.getTime()
    )

    let currentDate = new Date(startDate)
    for (const rateChange of rateChangesInPeriod) {
      const segmentDays = daysBetween(currentDate, rateChange.effectiveDate)
      if (segmentDays > 0) {
        const rate = this.getRateAtDate(currentDate)
        const segmentInterest = principal * (rate / 100) * (segmentDays / 365)
        totalInterest += segmentInterest
      }
      currentDate = new Date(rateChange.effectiveDate)
    }

    // Final segment - add +1 here for inclusive counting
    const finalDays = daysBetween(currentDate, endDate) + 1
    if (finalDays > 0) {
      const rate = this.getRateAtDate(currentDate)
      const segmentInterest = principal * (rate / 100) * (finalDays / 365)
      totalInterest += segmentInterest
    }

    // Weighted average rate
    const weightedAvgRate = (totalInterest / principal) * (365 / totalDays) * 100
    return [totalInterest, weightedAvgRate]
  }

  private calculateCompoundInterest(
    principal: number,
    startDate: Date,
    endDate: Date,
    compoundingFrequency: string
  ): [number, number] {
    // Add +1 for inclusive day counting
    const totalDays = daysBetween(startDate, endDate) + 1
    if (totalDays <= 0) {
      return [0, 0]
    }

    const periodsPerYear: Record<string, number> = {
      daily: 365,
      monthly: 12,
      quarterly: 4,
      'semi-annually': 2,
      annually: 1,
    }
    const n = periodsPerYear[compoundingFrequency] || 365

    if (this.isFlatRate) {
      const rate = this.flatRate / 100
      const t = totalDays / 365
      const amount = principal * Math.pow(1 + rate / n, n * t)
      const interest = amount - principal
      return [interest, this.flatRate]
    }

    // Variable rate: compound through each rate period
    let currentBalance = principal
    const rateChangesInPeriod = this.rateHistory.filter(
      (rc) => startDate < rc.effectiveDate && rc.effectiveDate <= endDate
    )
    rateChangesInPeriod.sort(
      (a, b) => a.effectiveDate.getTime() - b.effectiveDate.getTime()
    )

    let currentDate = new Date(startDate)

    for (const rateChange of rateChangesInPeriod) {
      const segmentDays = daysBetween(currentDate, rateChange.effectiveDate)
      if (segmentDays > 0) {
        const rate = this.getRateAtDate(currentDate) / 100
        const t = segmentDays / 365
        currentBalance = currentBalance * Math.pow(1 + rate / n, n * t)
      }
      currentDate = new Date(rateChange.effectiveDate)
    }

    // Final segment
    const finalDays = daysBetween(currentDate, endDate) + 1
    if (finalDays > 0) {
      const rate = this.getRateAtDate(currentDate) / 100
      const t = finalDays / 365
      currentBalance = currentBalance * Math.pow(1 + rate / n, n * t)
    }

    const interest = currentBalance - principal
    const tTotal = totalDays / 365
    const effectiveRate = (Math.pow(currentBalance / principal, 1 / tTotal) - 1) * 100

    return [interest, effectiveRate]
  }

  calculateInterest(
    principal: number,
    startDate: Date,
    endDate: Date,
    compoundingFrequency: string = 'daily'
  ): [number, number] {
    if (endDate < startDate) {
      throw new Error('End date must be after start date')
    }

    if (this.compounding === InterestCompounding.SIMPLE) {
      return this.calculateSimpleInterest(principal, startDate, endDate)
    } else {
      return this.calculateCompoundInterest(
        principal,
        startDate,
        endDate,
        compoundingFrequency
      )
    }
  }
}

// ============================================================================
// LATE INTEREST CALCULATOR
// ============================================================================

class LateInterestCalculator {
  private assumptions: FundAssumptions
  private rateCalculator: InterestRateCalculator

  constructor(assumptions: FundAssumptions) {
    this.assumptions = assumptions

    if (assumptions.lateInterestBase === InterestBase.PRIME) {
      this.rateCalculator = new InterestRateCalculator(
        assumptions.lateInterestCompounding,
        assumptions.primeRateHistory,
        assumptions.lateSpread
      )
    } else {
      this.rateCalculator = new InterestRateCalculator(
        assumptions.lateInterestCompounding,
        undefined,
        undefined,
        assumptions.flatRate
      )
    }
  }

  calculateLateInterestForNewLP(
    newLp: Partner,
    capitalCalls: CapitalCall[],
    compoundingFrequency: string = 'daily'
  ): NewLPCalculation {
    // Filter to capital calls that occurred before LP admission
    const missedCalls = capitalCalls
      .filter((call) => call.dueDate < newLp.issueDate)
      .sort((a, b) => a.callNumber - b.callNumber)

    const breakdown: LateInterestDetail[] = []
    let totalCatchUp = 0
    let totalLateInterest = 0

    for (const call of missedCalls) {
      const detail = this.calculateLateInterestForCall(newLp, call, compoundingFrequency)
      breakdown.push(detail)
      totalCatchUp += detail.capitalAmount
      totalLateInterest += detail.lateInterest
    }

    totalCatchUp = roundAmount(totalCatchUp, this.assumptions.sumRounding)
    totalLateInterest = roundAmount(totalLateInterest, this.assumptions.sumRounding)

    // Calculate management fee allocation using Excel formula
    let mgmtFeeAllocation = 0
    let mgmtFeeAudit: MgmtFeeAudit | undefined = undefined

    if (
      this.assumptions.mgmtFeeAllocatedInterest &&
      this.assumptions.mgmtFeeRate &&
      this.assumptions.mgmtFeeStartDate &&
      totalCatchUp > 0
    ) {
      // Calculate days from mgmt fee start date to LP issue date (+1 for inclusive)
      const daysForFee = daysBetween(this.assumptions.mgmtFeeStartDate, newLp.issueDate) + 1

      if (daysForFee > 0) {
        // Excel Formula: =IFERROR(ROUND(IF(C9="Yes",
        //   (($A5-$C$10+1)/365*$C$11) / ((SUM(J5:AC5)-G5)/D5) * G5,
        //   0), $C$15), 0)
        //
        // Where:
        // $A5 = issueDate
        // $C$10 = mgmtFeeStartDate
        // $C$11 = annualMgmtFeeRate
        // SUM(J5:AC5) = totalCatchUp + totalLateInterest
        // G5 = totalLateInterest
        // D5 = commitment
        // $C$15 = calcRounding

        const timeWeightedRate = (daysForFee / 365) * (this.assumptions.mgmtFeeRate / 100)
        const catchUpCapital = totalCatchUp // The capital portion (without interest)
        const catchUpRatio = catchUpCapital / newLp.commitment

        // Final formula: (timeWeightedRate / catchUpRatio) * totalLateInterest
        mgmtFeeAllocation = (timeWeightedRate / catchUpRatio) * totalLateInterest
        mgmtFeeAllocation = roundAmount(mgmtFeeAllocation, this.assumptions.calcRounding)

        // Create audit trail
        mgmtFeeAudit = {
          mgmtFeeStartDate: this.assumptions.mgmtFeeStartDate,
          issueDate: newLp.issueDate,
          daysInPeriod: daysForFee,
          annualRate: this.assumptions.mgmtFeeRate,
          catchUpCapital,
          totalLateInterest,
          commitment: newLp.commitment,
          timeWeightedRate,
          catchUpRatio,
          calculatedFee: mgmtFeeAllocation,
          formula: `((${daysForFee}/365 × ${this.assumptions.mgmtFeeRate}%) / (${catchUpCapital.toFixed(2)}/${newLp.commitment.toFixed(2)})) × ${totalLateInterest.toFixed(2)}`,
          excelFormula: `=ROUND((($A5-$C$10+1)/365*$C$11)/((SUM(J5:AC5)-G5)/D5)*G5, $C$15)`
        }
      }
    }

    // LP allocation is total late interest minus mgmt fee
    const lpAllocation = roundAmount(totalLateInterest - mgmtFeeAllocation, this.assumptions.sumRounding)

    return {
      partnerName: newLp.name,
      issueDate: newLp.issueDate,
      commitment: newLp.commitment,
      closeNumber: newLp.closeNumber,
      totalCatchUp,
      totalLateInterestDue: totalLateInterest,
      mgmtFeeAllocation,
      lpAllocation,
      breakdownByCapitalCall: breakdown,
      mgmtFeeAudit,
    }
  }

  private calculateLateInterestForCall(
    newLp: Partner,
    call: CapitalCall,
    compoundingFrequency: string
  ): LateInterestDetail {
    // Calculate capital amount owed
    const capitalAmount = newLp.commitment * (call.callPercentage / 100)

    // Determine end date for interest calculation
    const endDate =
      this.assumptions.endDateCalculation === EndDateCalculation.ISSUE_DATE
        ? newLp.issueDate
        : call.dueDate

    // Calculate days late
    const daysLate = daysBetween(call.dueDate, endDate)

    if (daysLate <= 0) {
      return {
        callNumber: call.callNumber,
        dueDate: call.dueDate,
        callPercentage: call.callPercentage,
        capitalAmount: roundAmount(capitalAmount, this.assumptions.calcRounding),
        lateInterest: 0,
        daysLate: 0,
        effectiveRate: 0,
      }
    }

    // Calculate late interest
    const [lateInterest, effectiveRate] = this.rateCalculator.calculateInterest(
      capitalAmount,
      call.dueDate,
      endDate,
      compoundingFrequency
    )

    return {
      callNumber: call.callNumber,
      dueDate: call.dueDate,
      callPercentage: call.callPercentage,
      capitalAmount: roundAmount(capitalAmount, this.assumptions.calcRounding),
      lateInterest: roundAmount(lateInterest, this.assumptions.calcRounding),
      daysLate,
      effectiveRate: roundAmount(effectiveRate, this.assumptions.calcRounding),
    }
  }
}

// ============================================================================
// ALLOCATION CALCULATOR
// ============================================================================

class AllocationCalculator {
  private assumptions: FundAssumptions

  constructor(assumptions: FundAssumptions) {
    this.assumptions = assumptions
  }

  calculateAllocations(
    newLps: NewLPCalculation[],
    allPartners: Partner[],
    admittingCloseNumber: number
  ): [ExistingLPAllocation[], number] {
    // Determine existing partners
    const existingPartners = allPartners.filter(
      (p) => p.closeNumber < admittingCloseNumber
    )

    if (existingPartners.length === 0) {
      return [[], 0]
    }

    // Total amount to allocate to existing LPs (after mgmt fee)
    const totalToAllocate = newLps
      .filter((lp) => lp.closeNumber === admittingCloseNumber)
      .reduce((sum, lp) => sum + lp.lpAllocation, 0)

    if (totalToAllocate === 0) {
      return [[], 0]
    }

    // Total commitment of existing LPs
    const totalExistingCommitment = existingPartners.reduce(
      (sum, p) => sum + p.commitment,
      0
    )

    if (totalExistingCommitment === 0) {
      throw new Error('Total existing commitment cannot be zero')
    }

    // Build allocations
    const allocations: ExistingLPAllocation[] = []
    let totalAllocated = 0

    for (const partner of existingPartners) {
      const proRataPercentage = partner.commitment / totalExistingCommitment
      const allocationAmount = totalToAllocate * proRataPercentage
      const roundedAllocation = roundAmount(
        allocationAmount,
        this.assumptions.calcRounding
      )

      allocations.push({
        partnerName: partner.name,
        commitment: partner.commitment,
        closeNumber: partner.closeNumber,
        totalAllocation: roundedAllocation,
        allocationByAdmittingClose: {
          [admittingCloseNumber]: roundedAllocation,
        },
      })

      totalAllocated += roundedAllocation
    }

    totalAllocated = roundAmount(totalAllocated, this.assumptions.sumRounding)

    return [allocations, totalAllocated]
  }

  aggregateAllocationsAcrossCloses(
    allocationsByClose: Record<number, ExistingLPAllocation[]>
  ): ExistingLPAllocation[] {
    // Use composite key (partnerName + closeNumber) to keep separate rows
    const partnerAllocations: Record<string, ExistingLPAllocation> = {}

    for (const [closeNum, allocations] of Object.entries(allocationsByClose)) {
      for (const allocation of allocations) {
        // Create unique key for partner + their close number
        const compositeKey = `${allocation.partnerName}_${allocation.closeNumber}`

        if (!partnerAllocations[compositeKey]) {
          partnerAllocations[compositeKey] = {
            partnerName: allocation.partnerName,
            commitment: allocation.commitment,
            closeNumber: allocation.closeNumber,
            totalAllocation: 0,
            allocationByAdmittingClose: {},
          }
        }

        const partnerAlloc = partnerAllocations[compositeKey]
        partnerAlloc.totalAllocation += allocation.totalAllocation
        partnerAlloc.allocationByAdmittingClose[Number(closeNum)] =
          allocation.totalAllocation
      }
    }

    // Round totals
    for (const partnerAlloc of Object.values(partnerAllocations)) {
      partnerAlloc.totalAllocation = roundAmount(
        partnerAlloc.totalAllocation,
        this.assumptions.sumRounding
      )
    }

    // Sort by partner name, then by close number
    return Object.values(partnerAllocations).sort((a, b) => {
      if (a.partnerName !== b.partnerName) {
        return a.partnerName.localeCompare(b.partnerName)
      }
      return a.closeNumber - b.closeNumber
    })
  }
}

// ============================================================================
// MAIN ENGINE
// ============================================================================

export class LateInterestEngine {
  private assumptions: FundAssumptions
  private lateCalc: LateInterestCalculator
  private allocCalc: AllocationCalculator

  constructor(assumptions: FundAssumptions) {
    this.assumptions = assumptions
    this.lateCalc = new LateInterestCalculator(assumptions)
    this.allocCalc = new AllocationCalculator(assumptions)
  }

  runCompleteCalculation(
    partners: Partner[],
    capitalCalls: CapitalCall[],
    compoundingFrequency: string = 'daily'
  ): EngineOutput {
    // Sort and group partners by close
    partners.sort((a, b) => a.closeNumber - b.closeNumber)
    const partnersByClose: Record<number, Partner[]> = {}

    for (const partner of partners) {
      if (!partnersByClose[partner.closeNumber]) {
        partnersByClose[partner.closeNumber] = []
      }
      partnersByClose[partner.closeNumber].push(partner)
    }

    const allCloses = Object.keys(partnersByClose)
      .map(Number)
      .sort((a, b) => a - b)
    const closesToProcess = allCloses.slice(1) // Skip first close

    // Track results
    const allNewLpResults: any[] = []
    const allAllocationsByClose: Record<number, ExistingLPAllocation[]> = {}
    let grandTotalCollected = 0
    let grandTotalAllocated = 0
    let grandTotalMgmtFee = 0
    const closeSummaries: any[] = []

    // Process each close
    for (const closeNum of closesToProcess) {
      const newLpsAtClose = partnersByClose[closeNum]
      const existingPartners = partners.filter((p) => p.closeNumber < closeNum)

      // Calculate late interest for new LPs
      const newLpCalcs: NewLPCalculation[] = []
      let totalCollected = 0
      let totalMgmtFee = 0

      for (const newLp of newLpsAtClose) {
        const calc = this.lateCalc.calculateLateInterestForNewLP(
          newLp,
          capitalCalls,
          compoundingFrequency
        )
        newLpCalcs.push(calc)
        totalCollected += calc.totalLateInterestDue
        totalMgmtFee += calc.mgmtFeeAllocation

        allNewLpResults.push({
          partner_name: calc.partnerName,
          close_number: calc.closeNumber,
          commitment: calc.commitment.toString(),
          issue_date: calc.issueDate.toISOString().split('T')[0],
          total_catch_up: calc.totalCatchUp.toString(),
          total_late_interest_due: calc.totalLateInterestDue.toString(),
          mgmt_fee_allocation: calc.mgmtFeeAllocation.toString(),
          lp_allocation: calc.lpAllocation.toString(),
          breakdown: calc.breakdownByCapitalCall.map((d) => ({
            call_number: d.callNumber,
            due_date: d.dueDate.toISOString().split('T')[0],
            call_percentage: d.callPercentage.toString(),
            capital_amount: d.capitalAmount.toString(),
            late_interest: d.lateInterest.toString(),
            days_late: d.daysLate,
            effective_rate: d.effectiveRate.toString(),
          })),
          mgmt_fee_audit: calc.mgmtFeeAudit ? {
            mgmt_fee_start_date: calc.mgmtFeeAudit.mgmtFeeStartDate?.toISOString().split('T')[0],
            issue_date: calc.mgmtFeeAudit.issueDate.toISOString().split('T')[0],
            days_in_period: calc.mgmtFeeAudit.daysInPeriod,
            annual_rate: calc.mgmtFeeAudit.annualRate.toString(),
            catch_up_capital: calc.mgmtFeeAudit.catchUpCapital.toString(),
            total_late_interest: calc.mgmtFeeAudit.totalLateInterest.toString(),
            commitment: calc.mgmtFeeAudit.commitment.toString(),
            time_weighted_rate: calc.mgmtFeeAudit.timeWeightedRate.toString(),
            catch_up_ratio: calc.mgmtFeeAudit.catchUpRatio.toString(),
            calculated_fee: calc.mgmtFeeAudit.calculatedFee.toString(),
            formula: calc.mgmtFeeAudit.formula,
            excel_formula: calc.mgmtFeeAudit.excelFormula,
          } : undefined,
        })
      }

      grandTotalCollected += totalCollected
      grandTotalMgmtFee += totalMgmtFee

      // Calculate allocations
      let allocations: ExistingLPAllocation[] = []
      let totalAllocated = 0

      if (existingPartners.length > 0 && totalCollected > 0) {
        ;[allocations, totalAllocated] = this.allocCalc.calculateAllocations(
          newLpCalcs,
          partners,
          closeNum
        )
        allAllocationsByClose[closeNum] = allocations
        grandTotalAllocated += totalAllocated
      }

      closeSummaries.push({
        close_number: closeNum,
        new_lps_count: newLpsAtClose.length,
        existing_lps_count: existingPartners.length,
        total_collected: totalCollected.toString(),
        total_allocated: totalAllocated.toString(),
        difference: (totalCollected - totalAllocated).toString(),
      })
    }

    // Aggregate allocations
    const aggregatedAllocations =
      Object.keys(allAllocationsByClose).length > 0
        ? this.allocCalc.aggregateAllocationsAcrossCloses(allAllocationsByClose)
        : []

    const existingLpsOutput = aggregatedAllocations.map((alloc) => ({
      partner_name: alloc.partnerName,
      commitment: alloc.commitment.toString(),
      close_number: alloc.closeNumber,
      total_allocation: alloc.totalAllocation.toString(),
      allocation_by_close: Object.fromEntries(
        Object.entries(alloc.allocationByAdmittingClose).map(([k, v]) => [
          k,
          v.toString(),
        ])
      ),
    }))

    return {
      fundName: this.assumptions.fundName,
      calculationDate: new Date().toISOString().split('T')[0],
      totalLateInterestCollected: grandTotalCollected.toString(),
      totalLateInterestAllocated: grandTotalAllocated.toString(),
      totalMgmtFeeAllocation: grandTotalMgmtFee.toString(),
      newLps: allNewLpResults,
      existingLps: existingLpsOutput,
      summaryByClose: closeSummaries,
      settings: {
        late_interest_base: this.assumptions.lateInterestBase,
        late_spread: this.assumptions.lateSpread.toString(),
        compounding: this.assumptions.lateInterestCompounding,
        end_date_calculation: this.assumptions.endDateCalculation,
        calc_rounding: this.assumptions.calcRounding,
        sum_rounding: this.assumptions.sumRounding,
        prime_rate: this.assumptions.primeRateHistory[0]?.rate.toString() || 'N/A',
        mgmt_fee_enabled: this.assumptions.mgmtFeeAllocatedInterest,
        mgmt_fee_rate: this.assumptions.mgmtFeeRate?.toString() || 'N/A',
      },
    }
  }
}

// ============================================================================
// PARSING UTILITIES
// ============================================================================

export function parseNaturalCurrency(value: string): number {
  if (!value || value.trim() === '') return 0

  const cleaned = value
    .toLowerCase()
    .replace(/\$/g, '')
    .replace(/,/g, '')
    .replace(/\s/g, '')
    .trim()

  if (cleaned === '' || cleaned === '-') return 0

  let multiplier = 1
  let numStr = cleaned

  if (cleaned.endsWith('m')) {
    multiplier = 1000000
    numStr = cleaned.slice(0, -1)
  } else if (cleaned.endsWith('k')) {
    multiplier = 1000
    numStr = cleaned.slice(0, -1)
  } else if (cleaned.endsWith('b')) {
    multiplier = 1000000000
    numStr = cleaned.slice(0, -1)
  }

  return parseFloat(numStr) * multiplier
}

export function parseFlexibleDate(dateStr: string): Date {
  if (!dateStr || dateStr.trim() === '') {
    throw new Error('Date string is empty')
  }

  // Try ISO format first
  const isoDate = new Date(dateStr)
  if (!isNaN(isoDate.getTime())) {
    return isoDate
  }

  // Try MM/DD/YY or MM/DD/YYYY
  const parts = dateStr.split('/')
  if (parts.length === 3) {
    let [month, day, year] = parts.map((p) => parseInt(p))

    // Handle 2-digit years
    if (year < 100) {
      year += year < 50 ? 2000 : 1900
    }

    return new Date(year, month - 1, day)
  }

  throw new Error(`Could not parse date: ${dateStr}`)
}
