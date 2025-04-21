import { RunsPage } from "@/components/run/runs-list-page";
import { fetchRunsByPolicyVersion } from "@/lib/actions";

export default async function Page(props) {
    const params = await props.params;
    return <RunsPage resourceId={params.policy_version_id} fetchRuns={fetchRunsByPolicyVersion} />;
}
