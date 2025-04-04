import WorkflowFrame from "@/workflow/workflow";

export default async function Page(props) {
    const { policy_version_id } = await props.params;

    console.log("[policy version page] Policy Version ID:", policy_version_id);
    return <WorkflowFrame policyVersionId={policy_version_id} />;
}
