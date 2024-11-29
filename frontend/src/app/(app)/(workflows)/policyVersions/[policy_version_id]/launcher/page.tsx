"use server";

import { stackServerApp } from "@/stack";
import { fetchPolicyVersion, getAuthHeaders } from "@/lib/api";
import { LauncherPage } from "./components";
import { postLaunchFormAction } from "./actions";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const authHeaders = await getAuthHeaders(user);
    
    const policyVersion = await fetchPolicyVersion(user, params.policy_version_id);

    const graphDefinition = await JSON.parse(policyVersion.graph_definition);
    const inputSchema = graphDefinition.input_node.metadata.schema;

    return (
        <LauncherPage
            authHeaders={authHeaders}
            policyVersionId={params.policy_version_id}
            inputSchema={inputSchema}
            configVariables={policyVersion.config_variables}
            launchFn={postLaunchFormAction}
        />
    );
}
