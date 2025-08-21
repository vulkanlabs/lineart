import type { NodeDefinitionDict, PolicyVersion, RunData, RunLogs } from "@vulkanlabs/client-open";
import { fetchPolicyVersion, fetchRunData, fetchRunLogs } from "@/lib/api";

import type { NodeLayoutConfig, VulkanNode } from "@vulkanlabs/base";
import { createWorkflowState, getLayoutedNodes, defaultElkOptions } from "@vulkanlabs/base";

import RunPageContent from "@/components/run/run-page-content";
import type { RunNodeLayout } from "@/components/run/types";

export async function RunPage({ runId }: { runId: string }) {
    const runLogs: RunLogs = await fetchRunLogs(runId);
    const runData: RunData = await fetchRunData(runId);

    const graphDefinition = await getGraphDefinition(runData.policy_version_id);
    const workflowState = createWorkflowState(graphDefinition);
    const layoutedNodes = await getLayoutedNodes(workflowState.nodes, workflowState.edges);

    const runNodes: RunNodeLayout[] = layoutedNodes.map((node: VulkanNode) => {
        const runNode = {
            ...node,
            data: {
                ...node.data,
                run: runData.steps[node.id] || null,
            },
        };
        return runNode;
    });

    return (
        <RunPageContent
            nodes={runNodes}
            edges={workflowState.edges}
            runLogs={runLogs}
            runData={runData}
        />
    );
}

async function getGraphDefinition(
    policyVersionId: string,
): Promise<Array<NodeDefinitionDict | null>> {
    const policyVersion: PolicyVersion = await fetchPolicyVersion(policyVersionId);
    let nodes: Array<NodeDefinitionDict | null> = policyVersion?.workflow?.spec.nodes || [];
    if (nodes.length > 0) nodes.push(inputNode);
    return nodes;
}

const inputNode: NodeDefinitionDict = {
    name: "input_node",
    node_type: "INPUT",
    dependencies: null,
    metadata: null,
};
