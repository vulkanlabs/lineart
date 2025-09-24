import { RunsPage } from "@vulkanlabs/base/components/runs";
import { fetchPolicyVersionRuns } from "@/lib/api";

export default async function Page(props: { params: Promise<{ policy_version_id: string }> }) {
    const params = await props.params;
    const { policy_version_id } = params;
    return <RunsPage resourceId={policy_version_id} fetchRuns={fetchPolicyVersionRuns} />;
}
