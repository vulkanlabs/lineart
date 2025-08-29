import { RunsPage } from "@vulkanlabs/base";
import { fetchRunsByPolicy } from "@/lib/api-client";

export default async function Page(props: { params: Promise<{ policy_id: string }> }) {
    const params = await props.params;
    const { policy_id } = params;
    return <RunsPage resourceId={policy_id} fetchRuns={fetchRunsByPolicy} />;
}
