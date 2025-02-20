import { Suspense } from "react";
import { stackServerApp } from "@/stack";

import Loader from "@/components/loader";
import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";

import { AllocatedVersionsTable } from "./_components/table";

export default async function Page(props) {
    const params = await props.params;
    const policyId = params.policy_id;

    const user = await stackServerApp.getUser();
    const policyData = await fetchPolicy(user, policyId);
    const policyVersionsData = await fetchPolicyVersions(user, policyId).catch((error) => {
        console.error(error);
        return [];
    });
    const allocatedIds = getAllocatedVersions(policyData);
    const allocatedVersions = policyVersionsData.filter((policyVersion) =>
        allocatedIds.includes(policyVersion.policy_version_id),
    );

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <h1 className="text-lg font-semibold md:text-2xl">Allocated Versions</h1>
            <Suspense fallback={<Loader />}>
                <AllocatedVersionsTable policy={policyData} policyVersions={allocatedVersions} />
            </Suspense>
        </div>
    );
}

const getAllocatedVersions = (policyData) => {
    if (policyData.allocation_strategy == null) {
        return [];
    }
    const choiceVersions = policyData.allocation_strategy.choice.map((opt) => {
        return opt.policy_version_id;
    });
    return choiceVersions + policyData.allocation_strategy.shadow;
};
