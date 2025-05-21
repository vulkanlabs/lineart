import { Suspense } from "react";

import Loader from "@/components/animations/loader";
import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";
import { PolicyAllocationStrategy } from "@vulkan-server/PolicyAllocationStrategy";

import { AllocatedVersionsTable } from "./_components/table";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

export default async function Page(props: any) {
    const policyId = await props.params.policy_id;

    const policyData = await fetchPolicy(policyId);
    const allPolicyVersionsForPolicy = await fetchPolicyVersions(policyId).catch((error) => {
        console.error(error);
        return [];
    });

    const activeAndShadowVersionIds = getActiveAndShadowVersionIds(policyData?.allocation_strategy);

    const allocatedAndShadowVersionsToDisplay = allPolicyVersionsForPolicy.filter(
        (pv: PolicyVersion) => activeAndShadowVersionIds.includes(pv.policy_version_id),
    );

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <h1 className="text-lg font-semibold md:text-2xl">Policy Allocations</h1>
            <Suspense fallback={<Loader />}>
                <AllocatedVersionsTable
                    policy={policyData}
                    policyVersions={allPolicyVersionsForPolicy} // All versions for the dialog
                    allocatedAndShadowVersions={allocatedAndShadowVersionsToDisplay}
                />
            </Suspense>
        </div>
    );
}

// Get IDs of versions that are currently in the allocation strategy (choice or shadow)
const getActiveAndShadowVersionIds = (
    allocationStrategy: PolicyAllocationStrategy | null,
): string[] => {
    if (!allocationStrategy) {
        return [];
    }
    const choiceIds = allocationStrategy.choice.map((opt) => opt.policy_version_id);
    const shadowIds = allocationStrategy.shadow || [];
    return Array.from(new Set([...choiceIds, ...shadowIds]));
};
