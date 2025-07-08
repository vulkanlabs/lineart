import { RunsPage } from "@/components/run/runs-list-page";
import { fetchRunsByPolicy } from "@/lib/actions";

export default async function Page(props: { params: { policy_id: string } }) {
    return <RunsPage resourceId={props.params.policy_id} fetchRuns={fetchRunsByPolicy} />;
}
