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

import { VulkanNode, VulkanNodeType, GraphDefinition, BranchNodeMetadata } from "./types";
import { createNodeByType } from "./nodes";

type WorkflowState = {
    nodes: VulkanNode[];
    edges: Edge[];
};

type WorkflowActions = {
    getSpec: () => GraphDefinition;
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

const inputNode = createNodeByType({
    type: "INPUT",
    position: { x: 200, y: 200 },
});

const defaultState: WorkflowState = {
    nodes: [inputNode],
    edges: [],
};

type WorkflowStore = WorkflowState & WorkflowActions;

const createWorkflowStore = (initProps: WorkflowState = defaultState) => {
    return createStore<WorkflowStore>()((set, get) => ({
        ...initProps,

        getSpec: () => {
            const nodes = get().nodes;
            const edges = get().edges;

            const spec: GraphDefinition = {};

            nodes.forEach((node) => {
                spec[node.id] = {
                    name: node.data.name,
                    node_type: node.type,
                    // description: node.data.description,
                    metadata: node.data.metadata,
                };
            });

            edges.forEach((edge) => {
                const sourceNode = spec[edge.source];
                const targetNode = spec[edge.target];
                let output = null;

                if (sourceNode.node_type === "BRANCH") {
                    const metadata = sourceNode.metadata as BranchNodeMetadata;
                    output = metadata.choices[edge.sourceHandle];
                }

                if (sourceNode && targetNode) {
                    targetNode.dependencies = [
                        ...(targetNode.dependencies || []),
                        { node: sourceNode.name, output: output },
                    ];
                }
            });

            return spec;
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
            const newNode = createNodeByType({ type, position });

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
            const newEdge: Edge = {
                ...connection,
                id: `${connection.source}-${connection.target}`,
            };

            get().addEdge(newEdge);
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
