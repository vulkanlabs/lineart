"use server";

import { fetchPolicyVersion } from "@/lib/api";
import { LauncherPage } from "./components";
import { postLaunchFormAction } from "./actions";

export default async function Page(props: { params: { policy_version_id: string } }) {
    const policyVersion = await fetchPolicyVersion(props.params.policy_version_id);

    // TODO: we should redo this to use the new policy version definitions
    const inputSchema: Map<string, string> = new Map();

    return (
        <LauncherPage
            policyVersionId={props.params.policy_version_id}
            inputSchema={inputSchema}
            configVariables={policyVersion.variables || []}
            launchFn={postLaunchFormAction}
        />
    );
}
