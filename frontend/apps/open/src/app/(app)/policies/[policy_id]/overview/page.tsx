import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";

import { PolicyOverviewPage } from "./_components/overview";

export default async function Page(props: Promise<{ params: { policy_id: string } }>) {
    const { params } = await props;
    const policyId = params.policy_id;

    const policyData = await fetchPolicy(policyId);
    const policyVersionsData = await fetchPolicyVersions(policyId).catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <PolicyOverviewPage
            policyId={policyId}
            policyData={policyData}
            policyVersionsData={policyVersionsData}
        />
    );
}
