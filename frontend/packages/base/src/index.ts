// Re-export essential utilities
export * from "./lib/utils";
export * from "./lib/chart";

// Re-export API utilities
export * from "./lib/api";

// Re-export UI components
export { VulkanLogo } from "./components/logo";

// Re-export animations
export * from "./components/animations";

// Re-export charts (selective exports for better tree-shaking)
export { DatePickerWithRange } from "./components/charts/date-picker";
export { VersionPicker } from "./components/charts/version-picker";
// data-source-charts and policy-stats not currently used by apps

// Re-export reusable components
export * from "./components/combobox";
export * from "./components/data-table";
export * from "./components/details-button";
export {
    EnvironmentVariablesEditor,
    type EnvironmentVariablesEditorProps,
} from "./components/environment-variables-editor";
export * from "./components/resource-table";
export * from "./components/shortened-id";
export * from "./components/reactflow";

// Re-export layout components
export * from "./components/page-layout";
export * from "./components/inner-navbar";
export * from "./components/navigation";

// Re-export run components (safe exports only)
export {
    RunsPage,
} from "./components/run";
export type {
    BaseRunNodeLayout,
    BaseRunNodeData,
    RunLogEvent,
    RunLog,
    RunLogs,
} from "./components/run";

// Re-export workflow frame components
export * from "./components/app-workflow-frame";

// Re-export data source components
export * from "./components/data-sources";

// Re-export workflow components (selective exports for better tree-shaking)
// Core workflow components used by apps
export { 
  WorkflowFrame,
  WorkflowApiProvider,
  WorkflowDataProvider,
  createWorkflowApiClient,
} from "./workflow";

// Workflow utilities used by apps
export {
  makeGraphElements,
  layoutGraph,
  defaultElkOptions,
} from "./workflow";

// Workflow types used by apps
export type {
  NodeLayoutConfig,
  EdgeLayoutConfig,
  NodeDependency,
  RunFrameConfig,
  DataSource,
} from "./workflow";

// Re-export shared app components
export { RefreshButton } from "./components/refresh-button";

// Re-export policy components
export * from "./components/policies";

// Re-export analytics components
export * from "./components/analytics";

// Re-export components table
export * from "./components/components";
