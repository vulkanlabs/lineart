import type { NodeDefinitionDict, PolicyVersion, RunData, RunLogs } from "@vulkanlabs/client-open";
import { fetchPolicyVersion, fetchRunData, fetchRunLogs } from "@/lib/api";

import type { NodeLayoutConfig } from "@/lib/workflow/types";
import { makeGraphElements } from "@/lib/workflow/graph";

import RunPageContent from "@/components/run/run-page-content";
import type { RunNodeLayout } from "@/components/run/types";
import { defaultElkOptions } from "@/components/run/options";

export async function RunPage({ runId }: { runId: string }) {
    const runLogs: RunLogs = await fetchRunLogs(runId);
    const runData: RunData = await fetchRunData(runId);

    const graphDefinition = await getGraphDefinition(runData.policy_version_id);
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
    policyVersionId: string,
): Promise<Array<NodeDefinitionDict | null>> {
    const policyVersion: PolicyVersion = await fetchPolicyVersion(policyVersionId);
    let nodes: Array<NodeDefinitionDict | null> = policyVersion?.spec.nodes || [];
    if (nodes.length > 0) nodes.push(inputNode);
    return nodes;
}

const inputNode: NodeDefinitionDict = {
    name: "input_node",
    node_type: "INPUT",
    dependencies: null,
    metadata: null,
};
