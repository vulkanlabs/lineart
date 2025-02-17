import Loader from "@/components/loader";
import PolicyMetrics from "./_components/policy-metrics";
import { fetchMetricsData, fetchPolicyOutcomeStats } from "@/lib/actions";
import { stackServerApp } from "@/stack";
import { Suspense } from "react";
import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";
import { PolicyVersionsTable } from "@/components/policy-version/table";

export default async function Page(props: any) {
    const params = await props.params;
    const policyId = params.policy_id;

    const user = await stackServerApp.getUser();
    const policyData = await fetchPolicy(user, policyId);
    const policyVersionsData = await fetchPolicyVersions(user, policyId).catch((error) => {
        console.error(error);
        return [];
    });

    const activeVersions = policyVersionsData.filter(
        (policyVersion) => policyVersion.policy_version_id === policyData.active_policy_version_id,
    );

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <h1 className="text-lg font-semibold md:text-2xl">Active Policy Versions</h1>
            <PolicyVersionsTable policy={policyData} policyVersions={activeVersions} />
            <Suspense fallback={<Loader />}>
                <PolicyMetrics
                    policyId={policyId}
                    metricsLoader={fetchMetricsData}
                    outcomesLoader={fetchPolicyOutcomeStats}
                    versions={policyVersionsData}
                />
            </Suspense>
        </div>
    );
}
