import { fetchPolicyVersion } from "@/lib/api";
import { LauncherPage } from "./components";

export default async function Page(props: { params: Promise<{ policy_version_id: string }> }) {
    const params = await props.params;
    const { policy_version_id } = params;
    const policyVersion = await fetchPolicyVersion(policy_version_id);

    // TODO: we should redo this to use the new policy version definitions
    const inputSchema: Map<string, string> = new Map();

    return (
        <LauncherPage
            policyVersionId={policy_version_id}
            inputSchema={inputSchema}
            configVariables={policyVersion.variables || []}
        />
    );
}
