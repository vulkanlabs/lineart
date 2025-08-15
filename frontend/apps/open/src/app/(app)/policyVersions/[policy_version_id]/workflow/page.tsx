import { AppWorkflowFrame } from "@/components/workflow-frame";
import { fetchPolicyVersion } from "@/lib/api";

export default async function Page(props: { params: Promise<{ policy_version_id: string }> }) {
    const { policy_version_id } = await props.params;
    const policyVersion = await fetchPolicyVersion(policy_version_id);

    return <AppWorkflowFrame workflowData={policyVersion} projectId={policyVersion.project_id} />;
}
