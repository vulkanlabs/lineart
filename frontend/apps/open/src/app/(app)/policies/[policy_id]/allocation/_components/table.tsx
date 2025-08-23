"use client";

// Vulkan packages
import { SharedAllocatedVersionsTable, parseDate } from "@vulkanlabs/base";
import type { Policy, PolicyVersion } from "@vulkanlabs/client-open";

// Local imports
import { UpdateAllocationsDialog } from "./dialog";

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
