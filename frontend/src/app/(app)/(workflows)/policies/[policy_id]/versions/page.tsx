import { stackServerApp } from "@/stack";

import { fetchPolicy, fetchPolicyVersions } from "@/lib/api";
import { Suspense } from "react";
import { PolicyVersionsTable } from "@/components/policy-version/table";

export default async function Page(props) {
    const params = await props.params;
    const policyId = params.policy_id;

    const user = await stackServerApp.getUser();
    const policyData = await fetchPolicy(user, policyId);
    const policyVersionsData = await fetchPolicyVersions(user, policyId).catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex flex-col gap-4">
                <h1 className="text-lg font-semibold md:text-2xl">Versions</h1>
                <Suspense fallback={<div>Loading Table...</div>}>
                    <PolicyVersionsTable policy={policyData} policyVersions={policyVersionsData} />
                </Suspense>
            </div>
            <div className="flex flex-col gap-4">
                {/* <h1 className="text-lg font-semibold md:text-2xl">Experiments</h1> */}
            </div>
        </div>
    );
}
