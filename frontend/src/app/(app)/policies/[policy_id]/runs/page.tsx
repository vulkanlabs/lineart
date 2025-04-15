import { fetchPolicyRuns } from "@/lib/api";
import { RunsPage } from "@/components/run/runs-list-page";

export default async function Page(props) {
    const params = await props.params;
    const runs = await fetchPolicyRuns(params.policy_id).catch((error) => {
        console.error(error);
        return null;
    });

    return <RunsPage runs={runs} />;
}
