import ELK from "elkjs/lib/elk.bundled.js";

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

const NodeTypeMapping = {
    TRANSFORM: "transform",
    CONNECTION: "connection",
    DATA_INPUT: "data-input",
    BRANCH: "branch",
    TERMINATE: "terminate",
    INPUT: "input-node",
    COMPONENT: "component",
};

interface Dict {
    [key: string]: string | number | boolean;
}

interface NodeDefinition {
    name: string;
    node_type: string;
    description: string;
    dependencies: string[];
    hidden: boolean;
    metadata: any;
}

interface NodeDefinitionDict {
    [key: string]: NodeDefinition;
}

interface ComponentState {
    isOpen: boolean;
}

interface ComponentStateDict {
    [key: string]: ComponentState;
}

interface NodeLayoutConfig {
    id: string;
    data: {
        label: string;
        description: string;
        type: string;
        dependencies: string[];
    };
    width: number;
    height: number;
    type: string;
    parentId?: string;
    parentReference?: string;
    children?: NodeLayoutConfig[];
    layoutOptions?: Dict;
    targetPosition?: string;
    sourcePosition?: string;
    x?: number;
    y?: number;
}

interface EdgeLayoutConfig {
    id: string;
    source: string;
    target: string;
    isComponentIO: boolean;
    fromComponentChild?: boolean;
    fromComponent?: string;
    toComponentChild?: boolean;
    toComponent?: string;
}

/**
 * @param graphData - Raw data with the node definitions.
 * @param componentsState - State of the components (open or closed).
 * @param options - (optional) Layout options for the ELK algorithm.
 * @returns A Promise that returns the layouted nodes and edges of the graph.
 */
export default async function layoutGraph(
    graphData: NodeDefinitionDict,
    componentsState: ComponentStateDict,
    options: Dict = defaultElkOptions,
): Promise<[NodeLayoutConfig[], EdgeLayoutConfig[]]> {
    const [nodes, edges] = makeGraphElements(graphData, options);
    const elk = new ELK();

    let modifiedNodes = nodes.filter((node: NodeLayoutConfig) => {
        return !node.parentId || componentsState[node.parentId].isOpen;
    });
    modifiedNodes.forEach((node: NodeLayoutConfig) => {
        if (node.data.type === "COMPONENT" && !componentsState[node.id].isOpen) {
            node.children = [];
            node.type = NodeTypeMapping.COMPONENT;
        }
    });
    const modifiedEdges = edges.filter((edge: EdgeLayoutConfig) => {
        const fromChildOfClosedComponent =
            edge.fromComponentChild && !componentsState[edge.fromComponent].isOpen;
        const toChildOfClosedComponent =
            edge.toComponentChild && !componentsState[edge.toComponent].isOpen;
        return !(fromChildOfClosedComponent || toChildOfClosedComponent);
    });

    const [layoutedNodes, layoutedEdges] = await getLayoutedElements(
        modifiedNodes,
        modifiedEdges,
        elk,
        options,
    );

    return [layoutedNodes, layoutedEdges];
}

/**
 * @param graphData - Raw data with the node definitions.
 * @param options - Layout options for the ELK algorithm.
 * @returns A tuple with the nodes and edges of the graph.
 */
function makeGraphElements(
    graphData: { [key: string]: NodeDefinition },
    options: Dict,
): [NodeLayoutConfig[], EdgeLayoutConfig[]] {
    const rawNodes = Object.values(graphData);
    const structuredNodes = rawNodes.map((node: any) => makeNode(node, options));

    const flattenedNodes = structuredNodes.flatMap((n: NodeLayoutConfig) => flattenNodes(n));
    const nodesMap = Object.assign({}, ...flattenedNodes);

    const edges = rawNodes.flatMap((node: any) => makeEdges(node, nodesMap));

    return [structuredNodes, edges];
}

function makeNode(node: NodeDefinition, options: Dict, parent?: NodeDefinition): NodeLayoutConfig {
    // TODO: Make the node width and height dynamic.
    const nodeWidth = 210;
    const nodeHeight = 42;

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
        nodeConfig.children = Object.values(node.metadata.nodes).map((n: NodeDefinition) =>
            makeNode(n, options, node),
        );
        nodeConfig.layoutOptions = options;
        nodeConfig.type = "group";
        return nodeConfig;
    }

    if (Object.keys(NodeTypeMapping).includes(node.node_type)) {
        nodeConfig.type = NodeTypeMapping[node.node_type];
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

function makeEdges(node: NodeDefinition, nodesMap: any): any[] {
    if (node.dependencies === null) {
        return [];
    }

    function __makeEdges(node: NodeDefinition): EdgeLayoutConfig[] {
        return node.dependencies.flatMap((dep: any) => {
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

    if (node.node_type == "COMPONENT") {
        const innerNodes = Object.values(node.metadata.nodes);
        const innerEdges = innerNodes.flatMap((n: any) => makeEdges(n, nodesMap));
        return [...__makeEdges(node), ...innerEdges];
    }

    return __makeEdges(node);
}

function flattenNodes(node: NodeLayoutConfig): { [key: string]: NodeLayoutConfig }[] {
    if (node.children) {
        const flattenedNodes = node.children.flatMap((n: any) => flattenNodes(n));
        return [{ [node.id]: node }, ...flattenedNodes];
    }
    return [{ [node.id]: node }];
}

async function getLayoutedElements(
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

            const extractChildren = (node: NodeLayoutConfig) => {
                if (node.children) {
                    const children = node.children.flatMap((child: NodeLayoutConfig) =>
                        extractChildren(child),
                    );
                    return [format_node(node), ...children];
                }
                return format_node(node);
            };

            let nodes = layoutedGraph.children.flatMap((node: NodeLayoutConfig) =>
                extractChildren(node),
            );
            nodes = nodes.filter((node: NodeLayoutConfig) => node.id !== "all");

            return [nodes, edges];
        })
        .catch(console.error);
}
