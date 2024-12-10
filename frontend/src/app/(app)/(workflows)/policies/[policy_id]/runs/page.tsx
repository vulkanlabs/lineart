import { stackServerApp } from "@/stack";

import { fetchPolicyRuns } from "@/lib/api";
import { RunsTableComponent } from "@/components/run/runs-table";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const runs = await fetchPolicyRuns(user, params.policy_id).catch((error) => {
        console.error(error);
        return null;
    });

    return <RunsTableComponent runs={runs} />;
}
