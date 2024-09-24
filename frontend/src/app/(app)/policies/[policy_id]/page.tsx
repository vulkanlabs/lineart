import { stackServerApp } from "@/stack";

import {
    fetchPolicy,
    fetchPolicyVersions,
    fetchRunsCount,
    fetchRunDurationStats,
    fetchRunDurationByStatus,
} from "@/lib/api";
import PolicyMetrics from "./_components/policy-metrics";
import PolicyVersionsTable from "./_components/policy-versions";
import { LocalNavbar, LocalSidebar } from "./_components/navigation";

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
            policyVersion.status = "ativa";
        } else {
            policyVersion.status = "inativa";
        }
    });

    return (
        <div className="flex flex-row w-full h-full overflow-scroll">
            <LocalSidebar policyData={policyData} />
            <div className="flex flex-col w-full h-full overflow-scroll">
                <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
                    <PolicyVersionsTable policyVersions={policyVersionsData} />
                    <PolicyMetrics policyId={policyId} />
                </div>
            </div>
        </div>
    );
}
