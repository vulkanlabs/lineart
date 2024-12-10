import { stackServerApp } from "@/stack";

import WorkflowPage from "@/components/workflow/workflow";
import { fetchPolicyVersion } from "@/lib/api";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const policyVersion = await fetchPolicyVersion(user, params.policy_version_id);
    const graphData = JSON.parse(policyVersion.graph_definition);

    return <WorkflowPage graphData={graphData} />;
}
