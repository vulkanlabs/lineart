"use client";

import { type ReactNode, createContext, useRef, useContext } from "react";
import { createStore, useStore } from "zustand";
import {
    addEdge,
    applyEdgeChanges,
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
} from "./types";

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
};

type WorkflowStore = WorkflowState & WorkflowActions;

const createWorkflowStore = (initProps: WorkflowState) => {
    return createStore<WorkflowStore>()((set, get) => ({
        ...initProps,

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

                if (sourceNode && sourceNode.type === "BRANCH") {
                    const metadata = sourceNode.data.metadata as BranchNodeMetadata;
                    output = metadata.choices[edge.sourceHandle];
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
            console.log("Nodes:", get().nodes);
            console.log("Edges:", get().edges);
            console.log("Spec:", get().getSpec());
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
            const edgeId = `${connection.source}-${connection.target}`;
            const newEdge: Edge = { ...connection, id: edgeId };
            get().addEdge(newEdge);

            const nodes = get().nodes;
            const sourceNode = nodes.find((node) => node.id === connection.source);
            const targetNode = nodes.find((node) => node.id === connection.target);
            let output = null;

            if (sourceNode.type === "BRANCH") {
                const metadata = sourceNode.data.metadata as BranchNodeMetadata;
                output = metadata.choices[connection.sourceHandle];
            }

            const dependency = {
                node: sourceNode.data.name,
                output: output,
                key: null,
            };

            get().updateNodeData(connection.target, {
                ...targetNode.data,
                incomingEdges: {
                    ...targetNode.data.incomingEdges,
                    [edgeId]: { key: sourceNode.data.name, dependency },
                },
            });
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
