import { stackServerApp } from "@/stack";
import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";

import { PolicyOverviewPage } from "./_components/overview";

export default async function Page(props: any) {
    const params = await props.params;
    const policyId = params.policy_id;

    const user = await stackServerApp.getUser();
    const policyData = await fetchPolicy(user, policyId);
    const policyVersionsData = await fetchPolicyVersions(user, policyId).catch((error) => {
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
