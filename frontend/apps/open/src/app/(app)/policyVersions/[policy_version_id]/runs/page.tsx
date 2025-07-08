import { RunsPage } from "@/components/run/runs-list-page";
import { fetchRunsByPolicyVersion } from "@/lib/actions";

export default async function Page(props: { params: { policy_version_id: string } }) {
    return (
        <RunsPage
            resourceId={props.params.policy_version_id}
            fetchRuns={fetchRunsByPolicyVersion}
        />
    );
}
