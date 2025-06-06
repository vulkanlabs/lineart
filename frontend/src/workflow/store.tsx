"use client";

import { type ReactNode, createContext, useRef, useContext } from "react";
import { createStore, useStore } from "zustand";
import {
    addEdge,
    applyEdgeChanges,
    Connection,
    getOutgoers,
    getIncomers,
    applyNodeChanges,
    OnConnect,
    OnEdgesChange,
    OnNodesChange,
    XYPosition,
    type Edge,
} from "@xyflow/react";

import { createNodeByType } from "./nodes";
import {
    VulkanNode,
    VulkanNodeType,
    GraphDefinition,
    BranchNodeMetadata,
    WorkflowState,
    InputNodeMetadata,
    DecisionNodeMetadata,
} from "./types";
import { toast } from "sonner";

type WorkflowActions = {
    getSpec: () => GraphDefinition;
    getInputSchema: () => { [key: string]: string };
    updateTargetDeps: (sourceNodeId: string) => void;
    onNodesChange: OnNodesChange<VulkanNode>;
    setNodes: (nodes: VulkanNode[]) => void;
    addNode: (node: VulkanNode) => void;
    updateNodeData: (nodeId: string, newData: Partial<VulkanNode["data"]>) => void;
    removeNode: (nodeId: string) => void;
    addNodeByType: (type: VulkanNodeType, position: XYPosition) => null | string;
    getNodes: () => VulkanNode[];
    setEdges: (edges: Edge[]) => void;
    getEdges: () => Edge[];
    addEdge: (edge: Edge) => void;
    removeEdge: (edgeId: string) => void;
    onConnect: OnConnect;
    onEdgesChange: OnEdgesChange<Edge>;
    setCollapsedNodeHeight: (nodeId: string, height: number) => void;
    removeCollapsedNodeHeight: (nodeId: string) => void;
    toggleNodeDetails: (nodeId: string) => void;
    updateNode: (nodeId: string, updates: Partial<VulkanNode>) => void;
    toggleAllNodesCollapsed: () => void;
};

type WorkflowStore = WorkflowState & WorkflowActions;

const createWorkflowStore = (initProps: WorkflowState) => {
    return createStore<WorkflowStore>()((set, get) => ({
        ...initProps,

        collapsedNodeHeights: {},

        getInputSchema: () => {
            const nodes = get().nodes;

            for (const node of nodes) {
                if (node.type === "INPUT") {
                    const data = node.data.metadata as InputNodeMetadata;
                    return data.schema;
                }
            }
            throw new Error("No input node found");
        },

        getSpec: () => {
            const nodes = get().nodes || [];
            const spec: GraphDefinition = {};

            nodes.forEach((node) => {
                spec[node.id] = {
                    name: node.data.name,
                    node_type: node.type,
                    metadata: node.data.metadata,
                    dependencies: Object.values(node.data.incomingEdges).reduce(
                        (acc, depConfig) => {
                            acc[depConfig.key] = depConfig.dependency;
                            return acc;
                        },
                        {},
                    ),
                };
            });

            return spec;
        },

        updateTargetDeps: (sourceNodeId) => {
            const nodes = get().nodes || [];
            const edges = get().edges || [];

            const sourceNode = nodes.find((n) => n.id === sourceNodeId);
            const targetNodesIds = edges
                .filter((edge) => edge.source === sourceNodeId)
                .map((edge) => edge.target);

            const newNodes = nodes.map((node) => {
                if (!targetNodesIds.includes(node.id)) return node;

                const edge = edges.find(
                    (edge) => edge.source === sourceNodeId && edge.target === node.id,
                );
                let output = null;

                if (sourceNode) {
                    if (sourceNode.type === "BRANCH") {
                        const metadata = sourceNode.data.metadata as BranchNodeMetadata;
                        output = metadata.choices[edge.sourceHandle];
                    } else if (sourceNode.type === "DECISION") {
                        const metadata = sourceNode.data.metadata as DecisionNodeMetadata;
                        if (metadata.conditions && metadata.conditions[edge.sourceHandle]) {
                            output = metadata.conditions[edge.sourceHandle].output;
                        }
                    }
                }

                const depConfig = { ...node.data.incomingEdges[edge.id] };
                depConfig.dependency = {
                    node: sourceNode.data.name,
                    output: output,
                    key: null,
                };

                return {
                    ...node,
                    data: {
                        ...node.data,
                        incomingEdges: {
                            ...node.data.incomingEdges,
                            [edge.id]: depConfig,
                        },
                    },
                };
            });
            set({ nodes: newNodes });
        },

        onNodesChange: async (changes) => {
            const nextNodes = applyNodeChanges(changes, get().nodes);
            set({ nodes: nextNodes });
        },

        setNodes: (nodes) => set({ nodes }),

        addNode: (node) => {
            const nextNodes = [...get().nodes, node];
            set({ nodes: nextNodes });
        },

        updateNodeData: (nodeId, newData) => {
            const nextNodes = get().nodes.map((node) => {
                if (node.id === nodeId) {
                    return {
                        ...node,
                        data: {
                            ...node.data,
                            ...newData,
                        },
                    };
                }
                return node;
            });
            set({ nodes: nextNodes });
        },

        removeNode: (nodeId) => set({ nodes: get().nodes.filter((node) => node.id !== nodeId) }),

        addNodeByType: (type, position) => {
            const existingNodes = get().nodes;
            const newNode = createNodeByType({ type, position, existingNodes });

            if (!newNode) return null;

            get().addNode(newNode);
            return newNode.id;
        },

        getNodes: () => get().nodes,

        setEdges: (edges) => set({ edges }),

        getEdges: () => get().edges,

        addEdge: (edge) => {
            const nextEdges = addEdge(edge, get().edges);
            set({ edges: nextEdges });
        },

        removeEdge: (edgeId) => {
            set({ edges: get().edges.filter((edge) => edge.id !== edgeId) });
        },

        onEdgesChange: (changes) => {
            const nextEdges = applyEdgeChanges(changes, get().edges);
            set({ edges: nextEdges });
        },

        onConnect: (connection) => {
            const nodes = get().nodes;
            const sourceNode = nodes.find((node) => node.id === connection.source);
            const targetNode = nodes.find((node) => node.id === connection.target);
            let output = null;

            if (!isValidConnection(connection, nodes, get().edges)) {
                console.warn("Invalid connection");
                toast("Invalid connection", {
                    description:
                        "This connection would create a cycle or unsatisfiable dependencies.",
                    dismissible: true,
                });
                return;
            }

            if (sourceNode) {
                if (sourceNode.type === "BRANCH") {
                    const metadata = sourceNode.data.metadata as BranchNodeMetadata;
                    output = metadata.choices[connection.sourceHandle];
                } else if (sourceNode.type === "DECISION") {
                    const metadata = sourceNode.data.metadata as DecisionNodeMetadata;
                    if (metadata.conditions && metadata.conditions[connection.sourceHandle]) {
                        output = metadata.conditions[connection.sourceHandle].output;
                    }
                }
            }

            const dependency = {
                node: sourceNode.data.name,
                output: output,
                key: null,
            };

            const edgeId =
                output !== null
                    ? `${connection.source}[${output}-${connection.sourceHandle}]-${connection.target}`
                    : `${connection.source}-${connection.target}`;

            const newEdge: Edge = { ...connection, id: edgeId };
            get().addEdge(newEdge);

            get().updateNodeData(connection.target, {
                ...targetNode.data,
                incomingEdges: {
                    ...targetNode.data.incomingEdges,
                    [edgeId]: { key: sourceNode.data.name, dependency },
                },
            });
        },

        setCollapsedNodeHeight: (nodeId: string, height: number) => {
            set((state) => ({
                collapsedNodeHeights: {
                    ...state.collapsedNodeHeights,
                    [nodeId]: height,
                },
            }));
        },

        removeCollapsedNodeHeight: (nodeId: string) => {
            set((state) => {
                const { [nodeId]: removed, ...rest } = state.collapsedNodeHeights;
                return { collapsedNodeHeights: rest };
            });
        },

        toggleNodeDetails: (nodeId: string) => {
            const state = get();
            const node = state.nodes.find((n) => n.id === nodeId);
            if (!node) return;

            const currentHeight = node.height;
            const isCurrentlyExpanded = node.data.detailsExpanded ?? true;
            let updatedNode;

            if (isCurrentlyExpanded) {
                // Collapsing: save current height and set to 50
                state.setCollapsedNodeHeight(nodeId, currentHeight);
                updatedNode = {
                    ...node,
                    height: 50,
                    data: { ...node.data, detailsExpanded: false },
                };
            } else {
                // Expanding: restore original height
                const originalHeight = state.collapsedNodeHeights[nodeId] || node.data.minHeight;
                state.removeCollapsedNodeHeight(nodeId);
                updatedNode = {
                    ...node,
                    height: originalHeight,
                    data: { ...node.data, detailsExpanded: true },
                };
            }

            // Update the nodes
            const updatedNodes = state.nodes.map((n) => (n.id === nodeId ? updatedNode : n));
            set({ nodes: updatedNodes });

            // Trigger proper dimension change through onNodesChange
            state.onNodesChange([
                {
                    id: nodeId,
                    type: "dimensions",
                    dimensions: {
                        width: updatedNode.width || node.width,
                        height: updatedNode.height,
                    },
                },
            ]);
        },

        updateNode: (nodeId: string, updates: Partial<VulkanNode>) => {
            const nextNodes = get().nodes.map((node) => {
                if (node.id === nodeId) {
                    return {
                        ...node,
                        ...updates,
                    };
                }
                return node;
            });
            set({ nodes: nextNodes });
        },

        toggleAllNodesCollapsed: () => {
            const state = get();
            const nodes = state.nodes;

            // Check if all nodes are currently collapsed (detailsExpanded === false)
            const allCollapsed = nodes.every((node) => node.data.detailsExpanded === false);

            // Toggle all nodes to the opposite state
            const updatedNodes = nodes.map((node) => {
                const currentHeight = node.height;
                const isCurrentlyExpanded = node.data.detailsExpanded ?? true;

                if (allCollapsed) {
                    // Expanding all: restore original height
                    const originalHeight =
                        state.collapsedNodeHeights[node.id] || node.data.minHeight || currentHeight;
                    return {
                        ...node,
                        height: originalHeight,
                        data: { ...node.data, detailsExpanded: true },
                    };
                } else {
                    // Collapsing all: save current height and set to 50
                    if (isCurrentlyExpanded) {
                        state.setCollapsedNodeHeight(node.id, currentHeight);
                    }
                    return {
                        ...node,
                        height: 50,
                        data: { ...node.data, detailsExpanded: false },
                    };
                }
            });

            // Update nodes
            set({ nodes: updatedNodes });

            // Trigger dimension changes for all affected nodes
            const dimensionChanges = updatedNodes.map((node) => ({
                id: node.id,
                type: "dimensions" as const,
                dimensions: {
                    width: node.width || 320,
                    height: node.height,
                },
            }));

            state.onNodesChange(dimensionChanges);
        },
    }));
};

type WorkflowStoreApi = ReturnType<typeof createWorkflowStore>;

export const WorkflowContext = createContext<WorkflowStoreApi | null>(null);

export type WorkflowProviderProps = {
    children: ReactNode;
    initialState?: WorkflowState;
};

export function WorkflowProvider({ children, initialState }: WorkflowProviderProps) {
    const storeRef = useRef<WorkflowStoreApi>(null);

    if (!storeRef.current) {
        storeRef.current = createWorkflowStore(initialState);
    }

    return <WorkflowContext.Provider value={storeRef.current}>{children}</WorkflowContext.Provider>;
}

export function useWorkflowStore<T>(selector: (store: WorkflowStore) => T): T {
    const workflowContext = useContext(WorkflowContext);

    if (!workflowContext) {
        throw new Error("Missing WorkflowContext.Provider in the tree");
    }

    return useStore(workflowContext, selector);
}

// TODO: we can be more granular here and provide a more specific error message
// for each case by returning an object with all the issues.
function isValidConnection(connection: Connection, nodes: VulkanNode[], edges: Edge[]): boolean {
    const target = nodes.find((node) => node.id === connection.target);
    const hasCycle = (node: VulkanNode, visited = new Set()) => {
        if (visited.has(node.id)) return false;

        visited.add(node.id);

        for (const outgoer of getOutgoers(node, nodes, edges)) {
            if (outgoer.id === connection.source) return true;
            if (hasCycle(outgoer, visited)) return true;
        }
    };

    const satisfiable = (node: VulkanNode) => {
        const cumulativeDependencies = (node: VulkanNode, deps: Map<string, Set<string>>) => {
            const incomers = node.data.incomingEdges;

            for (const incomer of Object.values(incomers)) {
                if (!deps.has(incomer.key)) {
                    deps.set(incomer.key, new Set());
                }

                deps.get(incomer.key).add(incomer.dependency.output);
                const incomerNode = nodes.find((n) => n.id === incomer.dependency.node);
                cumulativeDependencies(incomerNode, deps);
            }
            return deps;
        };

        const deps = cumulativeDependencies(node, new Map());
        for (const [key, values] of deps) {
            if (values.size > 1) {
                console.warn(
                    `Node ${node.id} has multiple dependencies on node ${key}: ${Array.from(
                        values,
                    ).join(", ")}`,
                );
                return false;
            }
        }
        return true;
    };

    if (target.id === connection.source) return false;
    return !hasCycle(target) && satisfiable(target);
}
