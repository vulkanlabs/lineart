import { stackServerApp } from "@/stack";

import { fetchPolicyVersionRuns } from "@/lib/api";
import { RunsTable } from "@/components/run/runs-table";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const runs = await fetchPolicyVersionRuns(user, params.policy_version_id).catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <div className="flex flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Runs</h1>
            </div>
            <RunsTable runs={runs} />
        </div>
    );
}
