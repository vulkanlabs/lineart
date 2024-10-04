import { stackServerApp } from "@/stack";

import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";
import PolicyMetrics from "./_components/policy-metrics";
import PolicyVersionsTable from "./_components/policy-versions";
import { fetchMetricsData } from "@/lib/actions";

export default async function Page({ params }) {
    const policyId = params.policy_id;
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

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div>
                <h1 className="text-lg font-semibold md:text-2xl">Versions</h1>
                <PolicyVersionsTable policyVersions={policyVersionsData} />
            </div>
            <PolicyMetrics policyId={policyId} dataLoader={fetchMetricsData} />
        </div>
    );
}
