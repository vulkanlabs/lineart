import Loader from "@/components/loader";
import PolicyMetrics from "./_components/policy-metrics";
import { fetchMetricsData, fetchPolicyOutcomeStats } from "@/lib/actions";
import { fetchPolicyVersions } from "@/lib/api";
import { stackServerApp } from "@/stack";
import { Suspense } from "react";

export default async function Page(props: any) {
    const params = await props.params;
    const policyId = params.policy_id;

    const user = await stackServerApp.getUser();
    const policyVersions = await fetchPolicyVersions(user, policyId);

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <Suspense fallback={<Loader />}>
                <PolicyMetrics
                    policyId={policyId}
                    metricsLoader={fetchMetricsData}
                    outcomesLoader={fetchPolicyOutcomeStats}
                    versions={policyVersions}
                />
            </Suspense>
        </div>
    );
}
