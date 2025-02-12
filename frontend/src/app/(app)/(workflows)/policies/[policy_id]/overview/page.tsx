import PolicyMetrics from "./_components/policy-metrics";
import { fetchMetricsData, fetchPolicyOutcomeStats } from "@/lib/actions";

export default async function Page(props) {
    const params = await props.params;
    const policyId = params.policy_id;

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <PolicyMetrics
                policyId={policyId}
                metricsLoader={fetchMetricsData}
                outcomesLoader={fetchPolicyOutcomeStats}
            />
        </div>
    );
}
