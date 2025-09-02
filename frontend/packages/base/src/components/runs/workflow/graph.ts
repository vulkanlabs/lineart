import ELK from "elkjs/lib/elk.bundled.js";

import { NodeDefinitionDict } from "@vulkanlabs/client-open";

import { NodeLayoutConfig, NodeDefinition, EdgeLayoutConfig, Dict, LayoutedNode } from "./types";
import { defaultElkOptions } from "./options";

const NodeTypeMapping: Record<string, string> = {
    TRANSFORM: "common",
    CONNECTION: "common",
    DATA_INPUT: "common",
    BRANCH: "common",
    DECISION: "common",
    TERMINATE: "terminate",
    INPUT: "entry",
};

export async function layoutGraph(
    nodes: NodeLayoutConfig[],
    edges: EdgeLayoutConfig[],
    options: Dict,
): Promise<[NodeLayoutConfig[], EdgeLayoutConfig[]]> {
    const elk = new ELK();

    const [layoutedNodes, layoutedEdges] = await getLayoutedElements(nodes, edges, elk, options);
    return [layoutedNodes, layoutedEdges];
}

/**
 * @param graphData - Raw data with the node definitions.
 * @returns A tuple with the nodes and edges of the graph.
 */
export function makeGraphElements(
    graphNodes: Array<NodeDefinitionDict>,
): [NodeLayoutConfig[], EdgeLayoutConfig[]] {
    const nodes = structureNodes(graphNodes).map((n) => withLayoutOptions(n, defaultElkOptions));

    const nodesMap = Object.assign(
        {},
        ...nodes.flatMap((node: NodeLayoutConfig) => {
            return [{ [node.id]: node }];
        }),
    );
    const edges = graphNodes.flatMap((node: any) => makeEdges(node, nodesMap));

    return [nodes, edges];
}

function structureNodes(nodes: NodeDefinitionDict[]): NodeLayoutConfig[] {
    return nodes.map((node: any) => makeNode(node));
}

export function withLayoutOptions(n: NodeLayoutConfig, options: Dict): NodeLayoutConfig {
    return {
        ...n,
        layoutOptions: options,
    };
}

type NodeDimensions = {
    width: number;
    height: number;
};

const defaultNodeDimensions: NodeDimensions = {
    width: 210,
    height: 42,
};

export function makeNode(node: NodeDefinition, dimensions?: NodeDimensions): NodeLayoutConfig {
    const nodeWidth = dimensions?.width || defaultNodeDimensions.width;
    const nodeHeight = dimensions?.height || defaultNodeDimensions.height;

    let nodeConfig: NodeLayoutConfig = {
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
    };

    if (Object.keys(NodeTypeMapping).includes(node.node_type)) {
        nodeConfig.type = NodeTypeMapping[node.node_type];
    } else {
        nodeConfig.targetPosition = "left";
        nodeConfig.sourcePosition = "right";
    }

    if (node.metadata !== null) {
        nodeConfig.data.metadata = node.metadata;
    }

    return nodeConfig;
}

function makeEdges(node: NodeDefinitionDict, nodesMap: any): EdgeLayoutConfig[] {
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

        let edge: EdgeLayoutConfig = {
            id: `${dep}-${node.name}`,
            source: dep,
            target: node.name,
        };

        return edge;
    });
}

export async function getLayoutedElements(
    nodes: NodeLayoutConfig[],
    edges: EdgeLayoutConfig[],
    elk: any,
    options: Dict,
): Promise<[NodeLayoutConfig[], EdgeLayoutConfig[]]> {
    const graph = {
        id: "root",
        layoutOptions: options,
        children: [{ id: "all", layoutOptions: options, children: nodes }],
        edges: edges,
    };

    return elk
        .layout(graph)
        .then((layoutedGraph: any) => {
            const format_node = (node: NodeLayoutConfig): LayoutedNode => ({
                ...node,
                // React Flow expects a position property on the node instead of `x`
                // and `y` fields.
                position: { x: node.x || 0, y: node.y || 0 },
            });

            const extractChildren = (node: NodeLayoutConfig): LayoutedNode[] => {
                if (node.children) {
                    const children = node.children.flatMap((child: NodeLayoutConfig) =>
                        extractChildren(child),
                    );
                    return [format_node(node), ...children];
                }
                return [format_node(node)];
            };

            let nodes = layoutedGraph.children.flatMap((node: NodeLayoutConfig) =>
                extractChildren(node),
            );
            nodes = nodes.filter((node: NodeLayoutConfig) => node.id !== "all");

            return [nodes, edges];
        })
        .catch(console.error);
}
