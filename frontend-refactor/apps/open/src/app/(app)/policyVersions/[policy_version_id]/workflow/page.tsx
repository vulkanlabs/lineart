import WorkflowFrame from "@/workflow/workflow";
import { fetchPolicyVersion } from "@/lib/api";

export default async function Page(props) {
    const { policy_version_id } = await props.params;
    const policyVersion = await fetchPolicyVersion(policy_version_id);

    return <WorkflowFrame policyVersion={policyVersion} />;
}
