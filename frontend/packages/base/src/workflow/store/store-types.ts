import type { OnConnect, OnEdgesChange, OnNodesChange, XYPosition, Edge } from "@xyflow/react";
import type { PolicyDefinitionDictInput } from "@vulkanlabs/client-open";
import type { VulkanNode, VulkanNodeType, WorkflowState } from "../types/workflow";
import type { WorkflowApiClient } from "../api/types";

/**
 * Actions available in the workflow store
 */
export type WorkflowActions = {
    // Spec and schema operations
    getSpec: () => PolicyDefinitionDictInput;
    getInputSchema: () => { [key: string]: string };

    // Node operations
    updateTargetDeps: (sourceNodeId: string) => void;
    onNodesChange: OnNodesChange<VulkanNode>;
    setNodes: (nodes: VulkanNode[]) => void;
    addNode: (node: VulkanNode) => void;
    updateNodeData: (nodeId: string, newData: Partial<VulkanNode["data"]>) => void;
    removeNode: (nodeId: string) => void;
    addNodeByType: (type: VulkanNodeType, position: XYPosition) => null | string;
    getNodes: () => VulkanNode[];
    updateNode: (nodeId: string, updates: Partial<VulkanNode>) => void;

    // Edge operations
    setEdges: (edges: Edge[]) => void;
    getEdges: () => Edge[];
    addEdge: (edge: Edge) => void;
    removeEdge: (edgeId: string) => void;
    onConnect: OnConnect;
    onEdgesChange: OnEdgesChange<Edge>;

    // UI state operations
    setCollapsedNodeHeight: (nodeId: string, height: number) => void;
    removeCollapsedNodeHeight: (nodeId: string) => void;
    toggleNodeDetails: (nodeId: string) => void;
    toggleAllNodesCollapsed: () => void;

    // Auto-save operations
    markChanged: () => void;
    markSaving: () => void;
    markSaved: () => void;
    markSaveError: (error: string) => void;
    clearSaveError: () => void;
    toggleAutoSave: () => void;
};

/**
 * Complete workflow store interface
 */
export type WorkflowStore = WorkflowState & WorkflowActions;

/**
 * Configuration for creating a workflow store
 */
export type WorkflowStoreConfig = {
    initialState: WorkflowState;
    apiClient: WorkflowApiClient;
};

/**
 * Type for the workflow store API
 */
export type WorkflowStoreApi = ReturnType<typeof import("./workflow-store").createWorkflowStore>;
