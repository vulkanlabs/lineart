import { RunsPage } from "@vulkanlabs/base";
import { fetchRunsByPolicyVersionClient } from "@/lib/api-client";

export default async function Page(props: { params: Promise<{ policy_version_id: string }> }) {
    const params = await props.params;
    const { policy_version_id } = params;
    return <RunsPage resourceId={policy_version_id} fetchRuns={fetchRunsByPolicyVersionClient} />;
}
