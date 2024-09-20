import { stackServerApp } from "@/stack";

import WorkflowPage from "@/components/workflow/workflow";
import { fetchPolicyVersionData } from "@/lib/api";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const graphData = await fetchPolicyVersionData(user, params.policy_id)
        .then((data) => {
            return JSON.parse(data.graph_definition);
        })
        .catch((error) => {
            console.error(error);
        });

    return <WorkflowPage graphData={graphData} />;
}
