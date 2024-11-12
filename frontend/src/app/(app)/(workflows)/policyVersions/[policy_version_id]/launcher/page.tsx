"use server";

import { stackServerApp } from "@/stack";
import { fetchPolicyVersion } from "@/lib/api";
import { LauncherPage } from "./components";
import { postLaunchFormAction } from "./actions";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const policyVersion = await fetchPolicyVersion(user, params.policy_version_id);

    const graphDefinition = await JSON.parse(policyVersion.graph_definition);
    const inputSchema = graphDefinition.input_node.metadata.schema;

    return (
        <LauncherPage
            policyVersionId={params.policy_version_id}
            inputSchema={inputSchema}
            configVariables={policyVersion.config_variables}
            launchFn={postLaunchFormAction}
        />
    );
}
