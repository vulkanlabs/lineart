import { stackServerApp } from "@/stack";

import WorkflowPage from "@/components/workflow/workflow";
import { fetchPolicy, fetchPolicyVersionData } from "@/lib/api";
import { LocalSidebar } from "./components";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const policyData = await fetchPolicy(user, params.policy_id);
    const graphData = await fetchPolicyVersionData(user, params.policy_id)
        .then((data) => {
            return JSON.parse(data.graph_definition);
        })
        .catch((error) => {
            console.error(error);
        });

    return (
        <div className="flex flex-row w-full h-full">
            <LocalSidebar policyData={policyData} />
            <WorkflowPage graphData={graphData} />
        </div>
    );
}
