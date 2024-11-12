import { CurrentUser } from "@stackframe/stack";

import { fetchPolicyVersion, fetchRun, fetchRunsData, fetchRunLogs } from "@/lib/api";

import RunPageContent from "@/components/run/run-page-content";
import type { GraphDefinition, NodeLayoutConfig } from "@/lib/workflow/types";
import { makeGraphElements } from "@/lib/workflow/graph";

import type { RunData, RunLogs, RunNodeLayout } from "@/components/run/types";
import { defaultElkOptions } from "@/components/run/options";

export async function RunPage({ user, runId }: { user: CurrentUser; runId: string }) {
    const runLogs: RunLogs = await fetchRunLogs(user, runId).catch((error) => {
        console.error(error);
        return {};
    });

    const runData: RunData = await fetchRunsData(user, runId).catch((error) => {
        console.error(error);
        return {};
    });

    const run = await fetchRun(user, runId).catch((error) => {
        console.error(error);
        return {};
    });

    const graphDefinition = await getGraphDefinition(user, run.policy_version_id);
    const [nodes, edges] = makeGraphElements(graphDefinition, defaultElkOptions);
    const flatNodes = nodes.reduce((acc: NodeLayoutConfig[], node) => {
        if (node.data.type === "COMPONENT") {
            return acc.concat(...node.children);
        }

        return acc.concat(node);
    }, []);

    const runNodes: RunNodeLayout[] = flatNodes.map((node: NodeLayoutConfig) => {
        const runNode = {
            ...node,
            data: {
                ...node.data,
                run: runData.steps[node.id] || null,
            },
        };
        return runNode;
    });

    return <RunPageContent nodes={runNodes} edges={edges} runLogs={runLogs} runData={runData} />;
}

async function getGraphDefinition(
    user: CurrentUser,
    policyVersionId: string,
): Promise<GraphDefinition> {
    const policyVersion = await fetchPolicyVersion(user, policyVersionId).catch((error) => {
        console.error(error);
    });
    const graphData: GraphDefinition = JSON.parse(policyVersion.graph_definition);

    return graphData;
}
