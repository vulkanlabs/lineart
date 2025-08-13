"use client";

// Vulkan packages
import { SharedAllocatedVersionsTable } from "@vulkanlabs/base";
import type { Policy, PolicyVersion } from "@vulkanlabs/client-open";

// Local imports
import { parseDate } from "@/lib/utils";
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
