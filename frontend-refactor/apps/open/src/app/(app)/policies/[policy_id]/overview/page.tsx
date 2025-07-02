import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";

import { PolicyOverviewPage } from "./_components/overview";

export default async function Page(props: any) {
    const params = await props.params;
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
