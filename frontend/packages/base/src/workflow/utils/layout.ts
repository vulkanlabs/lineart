import type { Edge } from "@xyflow/react";
import type { VulkanNode } from "../types/workflow";

/**
 * Default ELK layout options for automatic node positioning
 */
export const defaultElkOptions = {
    "elk.algorithm": "layered",
    "elk.layered.nodePlacement.strategy": "SIMPLE",
    "elk.layered.nodePlacement.bk.fixedAlignment": "BALANCED",
    "elk.layered.spacing.nodeNodeBetweenLayers": 50,
    "elk.spacing.nodeNode": 80,
    "elk.aspectRatio": 1.0,
    "elk.center": true,
    "elk.direction": "RIGHT",
};

/**
 * Type for nodes with layout options
 */
export type UnlayoutedVulkanNode = VulkanNode & {
    layoutOptions?: any;
};

/**
 * Apply automatic layout to workflow nodes using ELK algorithm
 *
 * Note: This function requires ELK.js to be available
 * Import: import ELK from "elkjs/lib/elk.bundled.js";
 */
export async function getLayoutedNodes(
    nodes: UnlayoutedVulkanNode[],
    edges: Edge[],
    options: any = defaultElkOptions,
): Promise<VulkanNode[]> {
    // Dynamic import to avoid bundling ELK if not needed
    const ELK = (await import("elkjs/lib/elk.bundled.js")).default;
    const elk = new ELK();

    // Convert ReactFlow edges to ELK format
    const elkEdges = edges.map((edge) => ({
        id: edge.id,
        sources: [edge.source],
        targets: [edge.target],
    }));

    const graph = {
        id: "root",
        layoutOptions: options,
        children: [
            {
                id: "all",
                layoutOptions: options,
                children: nodes,
            },
        ],
        edges: elkEdges,
    };

    try {
        const layoutedGraph = await elk.layout(graph);

        const formatNode = (node: any) => ({
            ...node,
            // React Flow expects a position property on the node instead of `x` and `y` fields.
            position: { x: node.x, y: node.y },
        });

        const extractChildren = (node: any): any[] => {
            if (node.children) {
                const children = node.children.flatMap((child: any) => extractChildren(child));
                return [formatNode(node), ...children];
            }
            return formatNode(node);
        };

        if (!layoutedGraph.children) {
            return nodes as VulkanNode[];
        }

        let layoutedNodes = layoutedGraph.children.flatMap((node: any) => extractChildren(node));
        layoutedNodes = layoutedNodes.filter((node: any) => node.id !== "all");

        return layoutedNodes as VulkanNode[];
    } catch (error) {
        console.error("Error applying layout:", error);
        throw error;
    }
}

/**
 * Check if automatic layout should be applied
 * Returns true if nodes don't have ui_metadata (indicating they need positioning)
 */
export function shouldApplyAutoLayout(uiMetadata: any): boolean {
    return !uiMetadata || Object.keys(uiMetadata).length === 0;
}
