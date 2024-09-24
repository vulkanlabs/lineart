import { stackServerApp } from "@/stack";

import WorkflowPage from "@/components/workflow/workflow";
import { fetchPolicyVersion } from "@/lib/api";
import { LocalSidebar } from "./components";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const policyVersion = await fetchPolicyVersion(user, params.policy_version_id).catch(
        (error) => {
            console.error(error);
        },
    );
    const graphData = JSON.parse(policyVersion.graph_definition);

    return (
        <div className="flex flex-row w-full h-full">
            <LocalSidebar policyVersion={policyVersion} />
            <WorkflowPage graphData={graphData} />
        </div>
    );
}
