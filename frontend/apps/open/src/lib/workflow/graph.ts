import ELK from "elkjs/lib/elk.bundled.js";
import { NodeDefinitionDict } from "@vulkanlabs/client-open";
import { NodeLayoutConfig, NodeDefinition, EdgeLayoutConfig, Dict } from "@/lib/workflow/types";

export const NodeTypeMapping = {
    TRANSFORM: "transform",
    CONNECTION: "connection",
    DATA_INPUT: "data-input",
    BRANCH: "branch",
    TERMINATE: "terminate",
    INPUT: "input-node",
    COMPONENT: "component",
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
 * @param options - Layout options for the ELK algorithm.
 * @returns A tuple with the nodes and edges of the graph.
 */
export function makeGraphElements(
    graphNodes: Array<NodeDefinitionDict>,
    options: Dict,
): [NodeLayoutConfig[], EdgeLayoutConfig[]] {
    const structuredNodes = structureNodes(graphNodes).map((n) => withLayoutOptions(n, options));
    const flattenedNodes = structuredNodes.flatMap(flattenNode);

    const nodesMap = Object.assign({}, ...flattenedNodes);

    const edges = graphNodes.flatMap((node: any) => makeEdges(node, nodesMap));

    return [structuredNodes, edges];
}

function structureNodes(nodes: NodeDefinitionDict[]): NodeLayoutConfig[] {
    const structuredNodes = nodes.map((node: any) => makeNode(node));
    return structuredNodes;
}

type NodeDimensions = {
    width: number;
    height: number;
};

const defaultNodeDimensions: NodeDimensions = {
    width: 210,
    height: 42,
};

export function makeNode(
    node: NodeDefinition,
    parent?: NodeDefinition,
    dimensions?: NodeDimensions,
): NodeLayoutConfig {
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

        // Hardcode a width and height for elk to use when layouting.
        width: nodeWidth,
        height: nodeHeight,
    };

    if (parent) {
        nodeConfig.parentId = parent.name;
        nodeConfig.parentReference = parent.metadata.reference;
    }

    if (node.node_type === "COMPONENT") {
        nodeConfig.children = Object.values(node.metadata.nodes || []).map((n: any) =>
            makeNode(n, node),
        ) as NodeLayoutConfig[];
        nodeConfig.type = "group";
        return nodeConfig;
    }

    if (Object.keys(NodeTypeMapping).includes(node.node_type)) {
        nodeConfig.type = NodeTypeMapping[node.node_type as keyof typeof NodeTypeMapping];
    } else {
        nodeConfig.targetPosition = "top";
        nodeConfig.sourcePosition = "bottom";
    }

    if (node.metadata !== null) {
        Object.entries(node.metadata).map(([key, value]) => {
            nodeConfig.data[key] = value;
        });
    }

    return nodeConfig;
}

export function withLayoutOptions(n: NodeLayoutConfig, options: Dict): NodeLayoutConfig {
    return {
        ...n,
        layoutOptions: options,
    };
}

function makeEdges(node: NodeDefinitionDict, nodesMap: any): any[] {
    if (node.dependencies === null) {
        return [];
    }

    function __makeEdges(node: NodeDefinitionDict): EdgeLayoutConfig[] {
        return Object.values(node.dependencies).flatMap((dep: any) => {
            // TODO: If `dep` is an object, it means that it comes from
            // a specific output of a node. For now, we discard it, as
            // we don't display the node outputs.
            if (typeof dep === "object" && dep !== null) {
                dep = dep.node;
            }

            const nodeDef = nodesMap[node.name];
            const depNode = nodesMap[dep];
            const isComponentIO =
                nodeDef.data.type === "COMPONENT" || depNode.data.type === "COMPONENT";

            let edge: EdgeLayoutConfig = {
                id: `${dep}-${node.name}`,
                source: dep,
                target: node.name,
                isComponentIO: isComponentIO,
            };

            if (nodeDef.parentId) {
                edge.toComponentChild = true;
                edge.toComponent = nodesMap[node.name].parentId;
            }

            // If the dependency is on the output of a Component, we need to
            // add an edge from the output node of the component.
            if (depNode.data.type === "COMPONENT") {
                const outputNode = depNode.children[depNode.children.length - 1];
                const childEdge = {
                    id: `${outputNode.id}-${node.name}`,
                    source: outputNode.id,
                    target: node.name,
                    isComponentIO: isComponentIO,
                    fromComponentChild: true,
                    fromComponent: depNode.id,
                    toComponentChild: edge.toComponentChild,
                    toComponent: edge.toComponent,
                };
                return [edge, childEdge];
            }

            // If the dependency a child of a Component, add both the edge
            // and an edge from the parent, used when the component is closed.
            if (depNode?.parentId) {
                edge.fromComponentChild = true;
                edge.fromComponent = depNode.parentId;

                if (nodeDef.parentId != depNode.parentId) {
                    const parentEdge = {
                        id: `${depNode.parentId}-${node.name}`,
                        source: depNode.parentId,
                        target: node.name,
                        isComponentIO: isComponentIO,
                    };
                    return [edge, parentEdge];
                }
            }

            return edge;
        });
    }

    return __makeEdges(node);
}

export function flattenNode(node: NodeLayoutConfig): { [key: string]: NodeLayoutConfig }[] {
    if (node.children) {
        const flattenedNodes = node.children.flatMap((n: any) => flattenNode(n));
        return [{ [node.id]: node }, ...flattenedNodes];
    }
    return [{ [node.id]: node }];
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
            const format_node = (node: NodeLayoutConfig) => ({
                ...node,
                // React Flow expects a position property on the node instead of `x`
                // and `y` fields.
                position: { x: node.x, y: node.y },
            });

            const extractChildren = (node: NodeLayoutConfig): NodeLayoutConfig[] => {
                if (node.children) {
                    return node.children.flatMap((child: NodeLayoutConfig) =>
                        extractChildren(child),
                    );
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
