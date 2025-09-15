"use client";

import { type ReactNode, createContext, useRef, useContext } from "react";
import { createStore, useStore } from "zustand";
import {
    addEdge,
    applyEdgeChanges,
    Connection,
    getOutgoers,
    applyNodeChanges,
    type Edge,
} from "@xyflow/react";
import { PolicyDefinitionDict } from "@vulkanlabs/client-open";

import type { WorkflowApiClient } from "../api/types";
import { AsNodeDefinitionDict, type VulkanNode, type WorkflowState } from "../types/workflow";
import type { InputNodeMetadata } from "../types/nodes";
import type { WorkflowStore, WorkflowStoreConfig, WorkflowStoreApi } from "./store-types";

import { createNodeByType } from "../utils/nodes";
import { findHandleNameByIndex } from "../utils/names";

// Toast function - this should be provided by the consuming application
declare function toast(message: string, options?: any): void;

/**
 * Create a Zustand store for workflow management with API client dependency injection
 */
export function createWorkflowStore(config: WorkflowStoreConfig) {
    const { initialState, autoSaveInterval = 10000 } = config; // Default to 10 seconds
    let markChangedTimer: NodeJS.Timeout | null = null;

    return createStore<WorkflowStore>()((set, get) => ({
        ...initialState,

        collapsedNodeHeights: initialState.collapsedNodeHeights || {},

        autoSave: initialState.autoSave || {
            lastSaved: null,
            isSaving: false,
            hasUnsavedChanges: false,
            saveError: null,
            autoSaveEnabled: true,
            retryCount: 0,
            autoSaveInterval,
            pendingChangesWhileSaving: false,
        },

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
            const spec: PolicyDefinitionDict = {
                nodes: nodes.filter((n) => n.type !== "INPUT").map(AsNodeDefinitionDict),
                input_schema: get().getInputSchema(),
            };

            return spec;
        },

        updateTargetDeps: (sourceNodeId) => {
            const nodes = get().nodes || [];
            const edges = get().edges || [];

            const sourceNode = nodes.find((n) => n.id === sourceNodeId);
            if (!sourceNode) return;

            const targetNodesIds = edges
                .filter((edge) => edge.source === sourceNodeId)
                .map((edge) => edge.target);

            const newNodes = nodes.map((node) => {
                if (!targetNodesIds.includes(node.id)) return node;

                const edge = edges.find(
                    (edge) => edge.source === sourceNodeId && edge.target === node.id,
                );
                if (!edge) return node;

                const output = findHandleNameByIndex(sourceNode, edge.sourceHandle || null);

                const existingDepConfig = node.data.incomingEdges?.[edge.id];
                const depConfig = {
                    key: existingDepConfig?.key || sourceNode.data.name!,
                    dependency: {
                        node: sourceNode.data.name!,
                        output: output,
                        key: null,
                    },
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
            const filteredChanges = changes.filter((change) => {
                if (change.type === "remove") {
                    const node = get().nodes.find((n) => n.id === change.id);
                    return node?.type !== "INPUT";
                }
                return true;
            });
            const nextNodes = applyNodeChanges(filteredChanges, get().nodes);
            set({ nodes: nextNodes });
            if (filteredChanges.length > 0) get().markChanged();
        },

        setNodes: (nodes) => {
            set({ nodes });
            get().markChanged();
        },

        addNode: (node) => {
            const nextNodes = [...get().nodes, node];
            set({ nodes: nextNodes });
            get().markChanged();
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
            get().markChanged();
        },

        removeNode: (nodeId) => {
            const node = get().nodes.find((n) => n.id === nodeId);
            if (node?.type === "INPUT") return;

            set({ nodes: get().nodes.filter((node) => node.id !== nodeId) });
            get().markChanged();
        },

        addNodeByType: (type, position) => {
            const existingNodes = get().nodes;
            const newNode = createNodeByType({ type, position, existingNodes });

            if (!newNode) return null;

            get().addNode(newNode);
            return newNode.id;
        },

        getNodes: () => get().nodes,

        setEdges: (edges) => {
            set({ edges });
            get().markChanged();
        },

        getEdges: () => get().edges,

        addEdge: (edge) => {
            const nextEdges = addEdge(edge, get().edges);
            set({ edges: nextEdges });
            get().markChanged();
        },

        removeEdge: (edgeId) => {
            set({ edges: get().edges.filter((edge) => edge.id !== edgeId) });
            get().markChanged();
        },

        onEdgesChange: (changes) => {
            const nextEdges = applyEdgeChanges(changes, get().edges);
            set({ edges: nextEdges });
            if (changes.length > 0) {
                get().markChanged();
            }
        },

        onConnect: (connection) => {
            const nodes = get().nodes;
            const sourceNode = nodes.find((node) => node.id === connection.source);
            const targetNode = nodes.find((node) => node.id === connection.target);

            if (!sourceNode || !targetNode) return;

            if (!isValidConnection(connection, nodes, get().edges)) {
                console.warn("Invalid connection");
                toast("Invalid connection", {
                    description:
                        "This connection would create a cycle or unsatisfiable dependencies.",
                    dismissible: true,
                });
                return;
            }

            const output = findHandleNameByIndex(sourceNode, connection.sourceHandle);

            const dependency = {
                node: sourceNode.data.name!,
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
                    [edgeId]: { key: sourceNode.data.name!, dependency },
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
                const { [nodeId]: removed, ...rest } = state.collapsedNodeHeights!;
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
                if (currentHeight) {
                    state.setCollapsedNodeHeight(nodeId, currentHeight);
                }
                updatedNode = {
                    ...node,
                    height: 50,
                    data: { ...node.data, detailsExpanded: false },
                };
            } else {
                // Expanding: restore original height
                const originalHeight =
                    state.collapsedNodeHeights?.[nodeId] || node.data.minHeight || 200;
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
                        width: updatedNode.width || node.width || 320,
                        height: updatedNode.height || 200,
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
            get().markChanged();
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
                        state.collapsedNodeHeights?.[node.id] ||
                        node.data.minHeight ||
                        currentHeight;
                    return {
                        ...node,
                        height: originalHeight,
                        data: { ...node.data, detailsExpanded: true },
                    };
                } else {
                    // Collapsing all: save current height and set to 50
                    if (isCurrentlyExpanded && currentHeight) {
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
                    height: node.height || 200,
                },
            }));

            state.onNodesChange(dimensionChanges);
            get().markChanged();
        },

        // Auto-save operations with configurable intervals
        markChanged: () => {
            // Debounce markChanged calls to prevent rapid-fire state updates
            if (markChangedTimer) clearTimeout(markChangedTimer);

            markChangedTimer = setTimeout(() => {
                const currentState = get();

                if (currentState.autoSave.isSaving) {
                    // If saving, mark that changes occurred during save
                    set((state) => ({
                        autoSave: {
                            ...state.autoSave,
                            pendingChangesWhileSaving: true,
                        },
                    }));
                } else {
                    // mark as having unsaved changes
                    set((state) => ({
                        autoSave: {
                            ...state.autoSave,
                            hasUnsavedChanges: true,
                            autoSaveInterval: autoSaveInterval, // Use configured interval
                        },
                    }));
                }
                markChangedTimer = null;
            }, 200);
        },

        markSaving: () => {
            set((state) => ({
                autoSave: {
                    ...state.autoSave,
                    isSaving: true,
                    saveError: null,
                },
            }));
        },

        markSaved: () => {
            set((state) => {
                // Check if changes were made while saving
                const hadPendingChanges = state.autoSave.pendingChangesWhileSaving;

                return {
                    autoSave: {
                        ...state.autoSave,
                        isSaving: false,
                        hasUnsavedChanges: hadPendingChanges, // Keep unsaved changes if they occurred during save
                        lastSaved: new Date(),
                        saveError: null,
                        retryCount: 0,
                        autoSaveInterval,
                        pendingChangesWhileSaving: false, // Reset  flag
                    },
                };
            });
        },

        markSaveError: (error: string) => {
            set((state) => {
                const newRetryCount = (state.autoSave.retryCount || 0) + 1;
                const maxRetries = 5;

                // Exponential backoff for retry intervals
                const retryDelay = Math.min(1000 * Math.pow(2, newRetryCount - 1), 30000);

                return {
                    autoSave: {
                        ...state.autoSave,
                        isSaving: false,
                        saveError: error,
                        retryCount: newRetryCount,
                        autoSaveInterval:
                            newRetryCount < maxRetries
                                ? retryDelay
                                : state.autoSave.autoSaveInterval,
                    },
                };
            });
        },

        clearSaveError: () => {
            set((state) => ({
                autoSave: {
                    ...state.autoSave,
                    saveError: null,
                    retryCount: 0, // Reset retry count when manually clearing
                },
            }));
        },

        toggleAutoSave: () => {
            set((state) => ({
                autoSave: {
                    ...state.autoSave,
                    autoSaveEnabled: !state.autoSave.autoSaveEnabled,
                },
            }));
        },
    }));
}

/**
 * React context for the workflow store
 */
export const WorkflowContext = createContext<WorkflowStoreApi | null>(null);

/**
 * Props for the WorkflowProvider component
 */
export type WorkflowStoreProviderProps = {
    children: ReactNode;
    initialState: WorkflowState;
    apiClient: WorkflowApiClient;
    autoSaveInterval?: number; // Optional auto-save interval in milliseconds, defaults to 10000 (10 seconds)
};

/**
 * Provider component that creates and provides a workflow store
 */
export function WorkflowStoreProvider({
    children,
    initialState,
    apiClient,
    autoSaveInterval = 10000, // Default to 10 seconds
}: WorkflowStoreProviderProps) {
    const storeRef = useRef<WorkflowStoreApi>(null);

    if (!storeRef.current)
        storeRef.current = createWorkflowStore({ initialState, apiClient, autoSaveInterval });

    return <WorkflowContext.Provider value={storeRef.current}>{children}</WorkflowContext.Provider>;
}

/**
 * Hook to access the workflow store
 */
export function useWorkflowStore<T>(selector: (store: WorkflowStore) => T): T {
    const workflowContext = useContext(WorkflowContext);

    if (!workflowContext)
        throw new Error("useWorkflowStore must be used within a WorkflowProvider");

    return useStore(workflowContext, selector);
}

/**
 * Connection validation function
 * TODO: we can be more granular here and provide a more specific error message
 * for each case by returning an object with all the issues.
 */
function isValidConnection(connection: Connection, nodes: VulkanNode[], edges: Edge[]): boolean {
    const target = nodes.find((node) => node.id === connection.target);
    if (!target) return false;

    const hasCycle = (node: VulkanNode, visited = new Set<string>()): boolean => {
        if (visited.has(node.id)) return false;

        visited.add(node.id);

        for (const outgoer of getOutgoers(node, nodes, edges)) {
            if (outgoer.id === connection.source) return true;
            if (hasCycle(outgoer, visited)) return true;
        }

        return false;
    };
    const satisfiable = (node: VulkanNode): boolean => {
        const cumulativeDependencies = (
            node: VulkanNode,
            deps: Map<string, Set<string>>,
        ): Map<string, Set<string>> => {
            const incomers = node.data.incomingEdges || {};

            for (const incomer of Object.values(incomers)) {
                const nodeDeps = deps.get(incomer.key) || new Set();
                nodeDeps.add(incomer.dependency.output || "");
                deps.set(incomer.key, nodeDeps);
                const incomerNode = nodes.find((n) => n.id === incomer.dependency.node);
                if (incomerNode) {
                    cumulativeDependencies(incomerNode, deps);
                }
            }
            return deps;
        };

        const deps = cumulativeDependencies(node, new Map());
        const sourceNode = nodes.find((n) => n.id === connection.source);
        if (!sourceNode) return false;

        if (sourceNode.type !== "BRANCH" && sourceNode.type !== "DECISION") {
            // For other node types, there is only one output, hence it's always valid.
            return true;
        }

        const sourceHandleName = findHandleNameByIndex(sourceNode, connection.sourceHandle);
        if (sourceHandleName === undefined || sourceHandleName === null) {
            return false;
        }

        const withNewDep = new Set(deps.get(connection.source) || []);
        withNewDep.add(sourceHandleName);

        if (withNewDep.size > 1) {
            console.warn(
                `Node ${node.id} already has dependencies on node ${connection.source}: ${Array.from(
                    withNewDep,
                ).join(", ")}`,
            );
            return false;
        }
        return true;
    };

    if (target.id === connection.source) return false;
    return !hasCycle(target) && satisfiable(target);
}
