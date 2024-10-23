import { stackServerApp } from "@/stack";
import { CurrentUser } from "@stackframe/stack";

import { fetchPolicyVersion, fetchRun, fetchRunsData, fetchRunLogs } from "@/lib/api";

import RunPageContent from "@/components/run/run-page-content";
import type {
    NodeDefinition,
    GraphDefinition,
    RunData,
    RunNode,
    RunLogs,
} from "@/components/run/types";

export async function RunPage({ user, runId}: { user: CurrentUser, runId: string }) {
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

    const flatNodes = await getNodeDefinitions(user, run.policy_version_id);

    const runGraph: RunNode[] = flatNodes.map((node: NodeDefinition) => {
        const runStep = runData.steps[node.name];
        return {
            ...node,
            run: runStep,
        };
    });

    return <RunPageContent runGraph={runGraph} runLogs={runLogs} />;
}

async function getNodeDefinitions(
    user: CurrentUser,
    policyVersionId: string,
): Promise<NodeDefinition[]> {
    const policyVersion = await fetchPolicyVersion(user, policyVersionId).catch((error) => {
        console.error(error);
    });
    const graphData: GraphDefinition = JSON.parse(policyVersion.graph_definition);

    const flatNodes: NodeDefinition[] = Object.values(graphData).flatMap((nodeDefinition) => {
        if (nodeDefinition.node_type === "COMPONENT") {
            return Object.values(nodeDefinition.metadata.nodes);
        }
        return [nodeDefinition];
    });

    return flatNodes;
}
