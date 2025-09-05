import type { PolicyVersion, RunData, RunLogs } from "@vulkanlabs/client-open";
import { fetchPolicyVersion, fetchRunData, fetchRunLogs } from "@/lib/api";

import { RunPageContent } from "@vulkanlabs/base";

export async function RunPage({ runId }: { runId: string }) {
    const runLogs: RunLogs = await fetchRunLogs(runId);
    const runData: RunData = await fetchRunData(runId);
    const policyVersion: PolicyVersion = await fetchPolicyVersion(runData.policy_version_id);
    const nodeDefinitions = policyVersion?.workflow?.spec.nodes || [];

    return (
        <RunPageContent
            nodeDefinitions={nodeDefinitions}
            runLogs={runLogs}
            runData={runData}
            config={{}}
        />
    );
}
