import { RunsPage } from "@vulkanlabs/base/components/runs";
import { fetchPolicyRuns } from "@/lib/api";

export default async function Page(props: { params: Promise<{ policy_id: string }> }) {
    const params = await props.params;
    const { policy_id } = params;
    return (
        <RunsPage
            resourceId={policy_id}
            resourcePathTemplate={"runs/{resourceId}"}
            fetchRuns={fetchPolicyRuns}
        />
    );
}
