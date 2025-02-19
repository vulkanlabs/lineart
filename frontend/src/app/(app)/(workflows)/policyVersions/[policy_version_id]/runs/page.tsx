import { stackServerApp } from "@/stack";

import { fetchPolicyVersionRuns } from "@/lib/api";
import { RunsPage } from "@/components/run/runs-list-page";

export default async function Page(props) {
    const params = await props.params;
    const user = await stackServerApp.getUser();
    const runs = await fetchPolicyVersionRuns(user, params.policy_version_id).catch((error) => {
        console.error(error);
        return [];
    });

    return <RunsPage runs={runs} />;
}
