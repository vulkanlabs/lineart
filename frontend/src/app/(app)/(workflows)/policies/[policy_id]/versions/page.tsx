import { stackServerApp } from "@/stack";

import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";
import PolicyMetrics from "./_components/policy-metrics";
import PolicyVersionsTable from "./_components/policy-versions";
import { fetchMetricsData } from "@/lib/actions";
import { Suspense } from "react";

export default async function Page(props) {
    const params = await props.params;
    const policyId = params.policy_id;

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div>
                <h1 className="text-lg font-semibold md:text-2xl">Versions</h1>
                <Suspense fallback={<div>Loading Table...</div>}>
                    <PolicyVersionsList policyId={policyId} />
                </Suspense>
            </div>
            <PolicyMetrics policyId={policyId} dataLoader={fetchMetricsData} />
        </div>
    );
}

async function PolicyVersionsList({ policyId }) {
    const user = await stackServerApp.getUser();
    const policyData = await fetchPolicy(user, policyId);
    const policyVersionsData = await fetchPolicyVersions(user, policyId).catch((error) => {
        console.error(error);
        return [];
    });

    policyVersionsData.forEach((policyVersion) => {
        if (policyVersion.policy_version_id === policyData.active_policy_version_id) {
            policyVersion.status = "active";
        } else {
            policyVersion.status = "inactive";
        }
    });

    return <PolicyVersionsTable policyVersions={policyVersionsData} />;
}
