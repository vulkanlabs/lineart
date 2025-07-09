"use server";

import { fetchPolicyVersion } from "@/lib/api";
import { LauncherPage } from "./components";
import { postLaunchFormAction } from "./actions";

export default async function Page(props: { params: Promise<{ policy_version_id: string }> }) {
    const { policy_version_id } = await props.params;
    const policyVersion = await fetchPolicyVersion(policy_version_id);

    // TODO: we should redo this to use the new policy version definitions
    const inputSchema: Map<string, string> = new Map();

    return (
        <LauncherPage
            policyVersionId={policy_version_id}
            inputSchema={inputSchema}
            configVariables={policyVersion.variables || []}
            launchFn={postLaunchFormAction}
        />
    );
}
