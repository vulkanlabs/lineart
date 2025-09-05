import ELK, { ElkNode, LayoutOptions } from "elkjs/lib/elk.bundled.js";
import { Position } from "@xyflow/react";

import { NodeDefinitionDict } from "@vulkanlabs/client-open";

import { ReactflowNode, ReactflowEdge, ELKLayoutedNode } from "./types";
import { nodeConfig, defaultElkOptions } from "./config";

/**
 * Convert raw node definitions into Reactflow nodes and edges.
 * @param nodes - Raw data with the node definitions.
 * @returns A tuple with the nodes and edges of the graph.
 */
export function makeGraphElements(
    nodes: Array<NodeDefinitionDict>,
): [ReactflowNode[], ReactflowEdge[]] {
    const rfNodes = nodes.map((node) => makeReactflowNode(node));

    // Create a map of nodes for easy lookup when creating edges
    const nodesMap = Object.assign({}, ...rfNodes.flatMap((node) => [{ [node.id]: node }]));
    const rfEdges = nodes.flatMap((node) => makeReactflowEdges(node, nodesMap));

    return [rfNodes, rfEdges];
}

type NodeDimensions = {
    width: number;
    height: number;
};

const defaultNodeDimensions: NodeDimensions = {
    width: 210,
    height: 42,
};

/**
 * Convert a NodeDefinitionDict to a ReactflowNode.
 * @param node - The node definition.
 * @param dimensions - Optional dimensions for the node.
 * @returns A ReactflowNode object.
 */
export function makeReactflowNode(
    node: NodeDefinitionDict,
    dimensions?: NodeDimensions,
): ReactflowNode {
    const nodeWidth = dimensions?.width || defaultNodeDimensions.width;
    const nodeHeight = dimensions?.height || defaultNodeDimensions.height;

    let reactflowNode: ReactflowNode = {
        id: node.name,
        data: {
            label: node.name,
            description: node.description,
            type: node.node_type,
            dependencies: node.dependencies,
        },
        type: "default",
        draggable: false,

        // Hardcode a width and height for elk to use when layouting.
        width: nodeWidth,
        height: nodeHeight,

        // Dummy positions, will be set by elk.
        position: { x: 0, y: 0 },
    };

    if (Object.keys(nodeConfig).includes(node.node_type)) {
        reactflowNode.type = nodeConfig[node.node_type].type;
    } else {
        reactflowNode.targetPosition = Position.Left;
        reactflowNode.sourcePosition = Position.Right;
    }

    if (node.metadata !== null) {
        reactflowNode.data.metadata = node.metadata;
    }

    return reactflowNode;
}

/** Convert node dependencies to Reactflow edges.
 * @param node - The node definition.
 * @param nodesMap - A map of node IDs to ReactflowNode objects.
 * @returns An array of ReactflowEdge objects.
 */
function makeReactflowEdges(node: NodeDefinitionDict, _nodesMap: any): ReactflowEdge[] {
    if (node.dependencies === null) {
        return [];
    }

    return Object.values(node.dependencies || {}).flatMap((dep: any) => {
        // TODO: If `dep` is an object, it means that it comes from
        // a specific output of a node. For now, we discard it, as
        // we don't display the node outputs.
        if (typeof dep === "object" && dep !== null) {
            dep = dep.node;
        }

        const edge: ReactflowEdge = {
            id: `${dep}-${node.name}`,
            source: dep,
            target: node.name,
        };

        return edge;
    });
}

/**
 * Layout nodes and edges using ELK algorithm
 * @param nodes - Array of ReactflowNode to be laid out
 * @param edges - Array of ReactflowEdge representing connections between nodes
 * @param elkOptions - Optional ELK layout options
 * @returns A promise that resolves to a tuple containing the layouted nodes and edges
 */
export async function layoutGraph(
    nodes: ReactflowNode[],
    edges: ReactflowEdge[],
    elkOptions: LayoutOptions = defaultElkOptions,
): Promise<[ReactflowNode[], ReactflowEdge[]]> {
    const elk = new ELK();

    const elkGraph: ElkNode = {
        id: "root",
        layoutOptions: elkOptions,
        children: [
            {
                id: "all",
                layoutOptions: elkOptions,
                // ReactflowNode is compatible with ElkNode
                children: nodes.map((n) => ({ ...n, layoutOptions: elkOptions })) as ElkNode[],
            },
        ],
        edges: edges.map((edge) => ({
            id: edge.id,
            sources: [edge.source],
            targets: [edge.target],
        })),
    };

    try {
        const layoutedGraph = await elk.layout(elkGraph);

        const formatNode = (node: ELKLayoutedNode): ReactflowNode => ({
            id: node.id,
            type: node.type,
            data: node.data,
            width: node.width,
            height: node.height,
            draggable: node.draggable,
            sourcePosition: node.sourcePosition,
            targetPosition: node.targetPosition,
            position: { x: node.x || 0, y: node.y || 0 },
        });

        // Extract all layouted nodes from the ELK result
        const layoutedNodes: ReactflowNode[] = [];

        // Get nodes from the "all" container
        const allContainer = layoutedGraph.children?.find((child) => child.id === "all");
        if (allContainer?.children) {
            for (const elkNode of allContainer.children) {
                // ELK keeps the original ReactflowNode properties and adds layout info
                const nodeWithPosition = elkNode as ELKLayoutedNode;
                layoutedNodes.push(formatNode(nodeWithPosition));
            }
        }

        return [layoutedNodes, edges];
    } catch (error) {
        console.error("ELK layout error:", error);
        throw error;
    }
}
