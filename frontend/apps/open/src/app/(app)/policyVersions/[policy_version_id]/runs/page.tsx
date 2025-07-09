import { RunsPage } from "@/components/run/runs-list-page";
import { fetchRunsByPolicyVersion } from "@/lib/actions";

export default async function Page(props: { params: Promise<{ policy_version_id: string }> }) {
    const { policy_version_id } = await props.params;
    return (
        <RunsPage
            resourceId={policy_version_id}
            fetchRuns={fetchRunsByPolicyVersion}
        />
    );
}
