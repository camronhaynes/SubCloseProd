"""
Allocation calculator for distributing late interest to existing LPs.
Handles pro-rata allocation based on commitment percentages and edge cases
for LPs increasing their commitments.
"""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Tuple
from ..models.data_models import (
    Partner,
    FundAssumptions,
    NewLPCalculation,
    ExistingLPAllocation
)


class AllocationCalculator:
    """
    Calculates pro-rata allocation of late interest to existing LPs.

    Pro-rata allocation is based on each LP's percentage ownership at the time
    of the new LP's admission. Special handling for LPs who increase their commitment
    (they receive allocation on their prior commitment, not their increase).
    """

    def __init__(self, assumptions: FundAssumptions):
        """
        Initialize with fund configuration.

        Args:
            assumptions: Fund-level calculation assumptions
        """
        self.assumptions = assumptions

    def calculate_allocations(
        self,
        new_lps: List[NewLPCalculation],
        all_partners: List[Partner],
        admitting_close_number: int
    ) -> Tuple[List[ExistingLPAllocation], Decimal]:
        """
        Calculate pro-rata allocations for all existing LPs based on new LP admissions.

        Args:
            new_lps: List of new LP calculations with late interest collected
            all_partners: Complete list of all partners in the fund
            admitting_close_number: The close number admitting the new LPs

        Returns:
            Tuple of (list of allocations per existing LP, total allocated amount)
        """
        # Determine which partners are "existing" at this close
        # Existing = joined before this close
        existing_partners = [
            p for p in all_partners
            if p.close_number < admitting_close_number
        ]

        if not existing_partners:
            # No existing partners to allocate to
            return [], Decimal('0')

        # Total late interest collected from all new LPs at this close
        total_late_interest = sum(
            new_lp.total_late_interest_due
            for new_lp in new_lps
            if new_lp.close_number == admitting_close_number
        )

        if total_late_interest == Decimal('0'):
            # No late interest to allocate
            return [], Decimal('0')

        # Calculate total commitment of existing LPs
        # This is the denominator for pro-rata calculation
        total_existing_commitment = sum(p.commitment for p in existing_partners)

        if total_existing_commitment == Decimal('0'):
            raise ValueError("Total existing commitment cannot be zero")

        # Build allocations for each existing LP
        allocations = []
        total_allocated = Decimal('0')

        for partner in existing_partners:
            # Pro-rata share = (LP's commitment / Total existing commitment)
            pro_rata_percentage = partner.commitment / total_existing_commitment

            # Allocation = Late interest collected × Pro-rata share
            allocation_amount = total_late_interest * pro_rata_percentage

            # Round according to fund settings
            allocation_amount = self._round_amount(
                allocation_amount,
                self.assumptions.calc_rounding
            )

            # Track by admitting close
            allocation_by_close = {admitting_close_number: allocation_amount}

            allocations.append(ExistingLPAllocation(
                partner_name=partner.name,
                commitment=partner.commitment,
                close_number=partner.close_number,
                total_allocation=allocation_amount,
                allocation_by_admitting_close=allocation_by_close
            ))

            total_allocated += allocation_amount

        # Round total according to fund settings
        total_allocated = self._round_amount(
            total_allocated,
            self.assumptions.sum_rounding
        )

        return allocations, total_allocated

    def calculate_allocations_with_increases(
        self,
        new_lps: List[NewLPCalculation],
        all_partners: List[Partner],
        commitment_increases: Dict[str, Decimal],
        admitting_close_number: int
    ) -> Tuple[List[ExistingLPAllocation], Decimal]:
        """
        Calculate allocations with special handling for LPs increasing commitments.

        When an LP increases their commitment at a subsequent close, they are both:
        1. An "existing LP" receiving allocation on their ORIGINAL commitment
        2. A "new LP" paying late interest on their INCREASED amount

        Args:
            new_lps: List of new LP calculations (includes increases)
            all_partners: Complete list of all partners
            commitment_increases: Map of partner name to their ORIGINAL commitment
                                 (before increase at this close)
            admitting_close_number: The close number admitting new LPs/increases

        Returns:
            Tuple of (list of allocations per existing LP, total allocated amount)

        Example:
            Partner A joined at Close 1 with $1M commitment
            At Close 2, Partner A increases to $2M (increase of $1M)

            For allocation purposes:
            - Partner A receives allocation on their $1M original commitment
            - Partner A pays late interest on the $1M increase
            - Other existing LPs also receive allocation pro-rata on their commitments
        """
        # Identify existing partners (joined before this close)
        existing_partners = [
            p for p in all_partners
            if p.close_number < admitting_close_number
        ]

        if not existing_partners:
            return [], Decimal('0')

        # Total late interest collected at this close
        total_late_interest = sum(
            new_lp.total_late_interest_due
            for new_lp in new_lps
            if new_lp.close_number == admitting_close_number
        )

        if total_late_interest == Decimal('0'):
            return [], Decimal('0')

        # For LPs with increases, use their ORIGINAL commitment for allocation
        # For LPs without increases, use their current commitment
        def get_allocation_commitment(partner: Partner) -> Decimal:
            """Get the commitment amount to use for allocation calculation"""
            if partner.name in commitment_increases:
                # Use original commitment (before increase)
                return commitment_increases[partner.name]
            else:
                # Use current commitment
                return partner.commitment

        # Calculate total commitment base for allocation
        total_existing_commitment = sum(
            get_allocation_commitment(p) for p in existing_partners
        )

        if total_existing_commitment == Decimal('0'):
            raise ValueError("Total existing commitment cannot be zero")

        # Build allocations
        allocations = []
        total_allocated = Decimal('0')

        for partner in existing_partners:
            allocation_commitment = get_allocation_commitment(partner)

            # Pro-rata share
            pro_rata_percentage = allocation_commitment / total_existing_commitment

            # Calculate allocation
            allocation_amount = total_late_interest * pro_rata_percentage
            allocation_amount = self._round_amount(
                allocation_amount,
                self.assumptions.calc_rounding
            )

            allocation_by_close = {admitting_close_number: allocation_amount}

            # Note: commitment shown is CURRENT commitment, not allocation base
            allocations.append(ExistingLPAllocation(
                partner_name=partner.name,
                commitment=partner.commitment,
                close_number=partner.close_number,
                total_allocation=allocation_amount,
                allocation_by_admitting_close=allocation_by_close
            ))

            total_allocated += allocation_amount

        total_allocated = self._round_amount(
            total_allocated,
            self.assumptions.sum_rounding
        )

        return allocations, total_allocated

    def aggregate_allocations_across_closes(
        self,
        allocations_by_close: Dict[int, List[ExistingLPAllocation]]
    ) -> List[ExistingLPAllocation]:
        """
        Aggregate allocations for each LP across multiple closes.

        Args:
            allocations_by_close: Map of close number to list of allocations at that close

        Returns:
            List of aggregated allocations, one per LP with totals across all closes
        """
        # Aggregate by partner name
        partner_allocations: Dict[str, ExistingLPAllocation] = {}

        for close_num, allocations in allocations_by_close.items():
            for allocation in allocations:
                partner_name = allocation.partner_name

                if partner_name not in partner_allocations:
                    # First time seeing this partner
                    partner_allocations[partner_name] = ExistingLPAllocation(
                        partner_name=partner_name,
                        commitment=allocation.commitment,
                        close_number=allocation.close_number,
                        total_allocation=Decimal('0'),
                        allocation_by_admitting_close={}
                    )

                # Add this close's allocation
                partner_alloc = partner_allocations[partner_name]
                partner_alloc.total_allocation += allocation.total_allocation
                partner_alloc.allocation_by_admitting_close[close_num] = (
                    allocation.total_allocation
                )

        # Round totals
        for partner_alloc in partner_allocations.values():
            partner_alloc.total_allocation = self._round_amount(
                partner_alloc.total_allocation,
                self.assumptions.sum_rounding
            )

        return list(partner_allocations.values())

    def _round_amount(self, amount: Decimal, decimal_places: int) -> Decimal:
        """
        Round a decimal amount to specified decimal places.

        Args:
            amount: Amount to round
            decimal_places: Number of decimal places

        Returns:
            Rounded amount
        """
        if decimal_places == 0:
            return amount.quantize(Decimal('1'))
        else:
            quantizer = Decimal('0.1') ** decimal_places
            return amount.quantize(quantizer)
