import { Suspense } from "react";

import { Loader } from "@vulkanlabs/base";
import { PolicyAllocationStrategy, PolicyVersion } from "@vulkanlabs/client-open";

import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";
import { AllocatedVersionsTable } from "./components";

export default async function Page(props: { params: Promise<{ policy_id: string }> }) {
    const params = await props.params;
    const { policy_id } = params;

    const policyData = await fetchPolicy(policy_id);
    const allPolicyVersionsForPolicy = await fetchPolicyVersions(policy_id).catch((error) => {
        console.error(error);
        return [];
    });

    const activeAndShadowVersionIds = getActiveAndShadowVersionIds(
        policyData?.allocation_strategy || null,
    );

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
