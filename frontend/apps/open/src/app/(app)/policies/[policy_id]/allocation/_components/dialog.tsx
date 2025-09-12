"use client";

import { UpdateAllocationDialog as SharedUpdateAllocationDialog } from "@vulkanlabs/base";
import type {
    PolicyAllocationStrategy,
    PolicyVersion,
} from "@vulkanlabs/client-open";

import { updatePolicyAllocationStrategy } from "@/lib/api";

export function UpdateAllocationsDialog({
    policyId,
    currentAllocation,
    policyVersions,
}: {
    policyId: string;
    currentAllocation: PolicyAllocationStrategy | null;
    policyVersions: PolicyVersion[];
}) {
    return (
        <SharedUpdateAllocationDialog
            config={{
                policyId,
                currentAllocation,
                policyVersions,
                updatePolicyAllocationStrategy,
            }}
        />
    );
}
