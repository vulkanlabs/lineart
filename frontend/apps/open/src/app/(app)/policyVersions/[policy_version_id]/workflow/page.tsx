import { AppWorkflowFrame } from "@/components/workflow-frame";
import { PROJECT_SCOPE_CONFIG } from "@vulkanlabs/base";
import { fetchPolicyVersion } from "@/lib/api";

export default async function Page(props: { params: Promise<{ policy_version_id: string }> }) {
    const params = await props.params;
    const { policy_version_id } = params;
    const policyVersion = await fetchPolicyVersion(policy_version_id);

    return (
        <AppWorkflowFrame
            workflowData={policyVersion}
            projectId={policyVersion.project_id}
            policyId={policyVersion.policy_id}
            config={PROJECT_SCOPE_CONFIG}
        />
    );
}
