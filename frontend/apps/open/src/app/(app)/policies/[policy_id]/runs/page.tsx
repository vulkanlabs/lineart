import { RunsPage } from "@/components/run/runs-list-page";
import { fetchRunsByPolicy } from "@/lib/actions";

export default async function Page(props: { params: Promise<{ policy_id: string }> }) {
    const { policy_id } = await props.params;
    return <RunsPage resourceId={policy_id} fetchRuns={fetchRunsByPolicy} />;
}
