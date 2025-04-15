"use server";

import { fetchPolicyVersion } from "@/lib/api";
import { LauncherPage } from "./components";
import { postLaunchFormAction } from "./actions";

export default async function Page(props) {
    const params = await props.params;

    const policyVersion = await fetchPolicyVersion(params.policy_version_id);

    // TODO: we should redo this to use the new policy version definitions
    const inputSchema = null;

    return (
        <LauncherPage
            policyVersionId={params.policy_version_id}
            inputSchema={inputSchema}
            configVariables={policyVersion.variables}
            launchFn={postLaunchFormAction}
        />
    );
}
