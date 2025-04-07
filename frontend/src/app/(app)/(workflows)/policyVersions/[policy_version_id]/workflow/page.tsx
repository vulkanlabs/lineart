import WorkflowFrame from "@/workflow/workflow";

export default async function Page(props) {
    const { policy_version_id } = await props.params;

    return <WorkflowFrame policyVersionId={policy_version_id} />;
}
