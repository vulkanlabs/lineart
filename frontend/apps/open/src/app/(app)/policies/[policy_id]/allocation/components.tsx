"use client";

// Vulkan packages
import type { Policy, PolicyVersion, PolicyAllocationStrategy } from "@vulkanlabs/client-open";
import {
    AllocatedVersionsTable as SharedAllocatedVersionsTable,
    UpdateAllocationDialog as SharedUpdateAllocationDialog,
    parseDate,
} from "@vulkanlabs/base";

// Local imports
import { updatePolicyAllocationStrategy } from "@/lib/api";

export function AllocatedVersionsTable({
    policy,
    policyVersions,
    allocatedAndShadowVersions,
}: {
    policy: Policy;
    policyVersions: PolicyVersion[];
    allocatedAndShadowVersions: PolicyVersion[];
}) {
    return (
        <SharedAllocatedVersionsTable
            policy={policy}
            policyVersions={policyVersions}
            allocatedAndShadowVersions={allocatedAndShadowVersions}
            config={{
                parseDate,
                UpdateAllocationsDialog,
            }}
        />
    );
}

function UpdateAllocationsDialog({
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
