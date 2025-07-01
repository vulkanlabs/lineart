import { NodeLayoutConfig, NodeDefinition, EdgeLayoutConfig, Dict } from "@/lib/workflow/types";
import { NodeTypeMapping, layoutGraph, makeGraphElements } from "@/lib/workflow/graph";
import { PolicyDefinitionDictOutput } from "@vulkan-server/PolicyDefinitionDictOutput";

/**
 * @param graphData - Raw data with the node definitions.
 * @param componentsState - State of the components (open or closed).
 * @param options - (optional) Layout options for the ELK algorithm.
 * @returns A Promise that returns the layouted nodes and edges of the graph.
 */
export async function makeWorkflow(
    graphData: PolicyDefinitionDictOutput,
    componentsState: ComponentStateDict,
    options: Dict = defaultElkOptions,
): Promise<[NodeLayoutConfig[], EdgeLayoutConfig[]]> {
    const [nodes, edges] = makeGraphElements(graphData.nodes, options);

    let modifiedNodes = nodes.filter((node: NodeLayoutConfig) => {
        return !node.parentId || componentsState[node.parentId].isOpen;
    });
    modifiedNodes.forEach((node: NodeLayoutConfig) => {
        if (node.data.type === "COMPONENT" && !componentsState[node.id].isOpen) {
            node.children = [];
            node.type = NodeTypeMapping["COMPONENT"];
        }
    });
    const modifiedEdges = edges.filter((edge: EdgeLayoutConfig) => {
        const fromChildOfClosedComponent =
            edge.fromComponentChild && !componentsState[edge.fromComponent].isOpen;
        const toChildOfClosedComponent =
            edge.toComponentChild && !componentsState[edge.toComponent].isOpen;
        return !(fromChildOfClosedComponent || toChildOfClosedComponent);
    });

    return layoutGraph(modifiedNodes, modifiedEdges, options);
}

interface NodeDefinitionDict {
    [key: string]: NodeDefinition;
}
interface ComponentStateDict {
    [key: string]: ComponentState;
}

interface ComponentState {
    isOpen: boolean;
}

const defaultElkOptions = {
    "elk.algorithm": "layered",
    "elk.layered.nodePlacement.strategy": "SIMPLE",
    "elk.layered.nodePlacement.bk.fixedAlignment": "BALANCED",
    "elk.layered.spacing.nodeNodeBetweenLayers": 50,
    "elk.spacing.nodeNode": 80,
    "elk.aspectRatio": 1.0,
    "elk.center": true,
    "elk.direction": "DOWN",
};
