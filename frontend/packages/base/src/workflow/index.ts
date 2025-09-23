// Main entry point for workflow functionality

// === Core Components ===
// Main workflow frame for embedding complete workflow functionality
// Note: WorkflowFrame is heavy component - exported as lazy from main index.ts for performance
export { WorkflowFrame } from "./components/workflow-frame";
export type { Workflow } from "./api/types";
export type { WorkflowFrameProps } from "./components/workflow-frame";

// Individual workflow components
export { WorkflowCanvas, WorkflowProviderWrapper } from "./components/workflow";
export type { WorkflowCanvasProps, WorkflowProviderWrapperProps } from "./components/workflow";

// Node components and types mapping
export { nodeTypes } from "./components/nodes";
export type {
    InputNode,
    TransformNode,
    BranchNode,
    DecisionNode,
    TerminateNode,
    PolicyNode,
    DataInputNode,
    ConnectionNode,
    ComponentNode,
} from "./components/nodes";

// === State Management ===
export {
    WorkflowStoreProvider as WorkflowProvider,
    useWorkflowStore,
    createWorkflowStore,
} from "./store";
export type { WorkflowStore, WorkflowStoreConfig } from "./store";

// === API Integration ===
export {
    WorkflowApiProvider,
    useWorkflowApi,
    DefaultWorkflowApiClient,
    createWorkflowApiClient,
} from "./api";
export type { WorkflowApiClient, SaveWorkflowResult } from "./api";

// === Data Management ===
export { WorkflowDataProvider, useWorkflowData } from "./context";
export type { WorkflowData, WorkflowDataProviderProps } from "./context";

// === Types ===
export type {
    VulkanNode,
    VulkanNodeData,
    VulkanNodeType,
    VulkanNodeProps,
    WorkflowState,
    NodeConfig,
    IncomingEdges,
    NodeDependency,
} from "./types/workflow";

// === Utilities ===
export { createWorkflowState } from "./utils/workflow-state";
export { createNodeByType, nodesConfig } from "./utils/nodes";
export { getLayoutedNodes, defaultElkOptions } from "./utils/layout";
export { standardizeNodeName, findHandleNameByIndex, findHandleIndexByName } from "./utils/names";

// === Icons ===
export { iconMapping } from "./icons";

// === Hooks ===
export { useDropdown } from "./hooks";
