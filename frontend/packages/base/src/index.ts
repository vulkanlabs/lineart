// Re-export essential utilities (selective exports for better tree-shaking)
export { parseDate } from "./lib/utils";
// Note: Other utils from "./lib/utils" not currently used by apps
export * from "./lib/chart";

// Re-export API utilities
export * from "./lib/api";

// Re-export UI components
export { VulkanLogo, type VulkanLogoConfig } from "./components/logo";

// Re-export animations (selective exports for better tree-shaking)
export { Loader, Sending } from "./components/animations";

// Re-export charts (selective exports for better tree-shaking)
export { DatePickerWithRange } from "./components/charts/date-picker";
export { VersionPicker } from "./components/charts/version-picker";
// data-source-charts and policy-stats not currently used by apps

// Re-export reusable components (selective exports for better tree-shaking)
export { DataTable } from "./components/data-table";
export { DetailsButton } from "./components/details-button";
export {
    EnvironmentVariablesEditor,
    type EnvironmentVariablesEditorProps,
} from "./components/environment-variables-editor";
export { ResourceTable } from "./components/resource-table";
export { ShortenedID } from "./components/shortened-id";
// Note: combobox and reactflow components not currently used by apps

// Re-export layout components (selective exports for better tree-shaking)
export { PageLayout, type PageLayoutConfig } from "./components/page-layout";
export { InnerNavbar, type InnerNavbarSectionProps } from "./components/inner-navbar";
export { SharedNavbar, type NavigationSection } from "./components/navigation";

// Re-export run components (safe exports only)
export {
    RunsPage,
} from "./components/run";
// Note: Run-related types (BaseRunNodeLayout, BaseRunNodeData, RunLogEvent, RunLog, RunLogs) 
// not currently used by apps - RunLogs comes from @vulkanlabs/client-open instead

// Re-export workflow frame components
export * from "./components/app-workflow-frame";

// Re-export data source components (selective exports for better tree-shaking)
export { 
  SharedCreateDataSourceDialog,
  type CreateDataSourceDialogConfig,
  DataSourcesTable as SharedDataSourcesTable,
} from "./components/data-sources";

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

// Re-export policy components (selective exports for better tree-shaking)
export { 
  CreatePolicyDialog as SharedCreatePolicyDialog,
  PoliciesTable as SharedPoliciesTable,
  SharedAllocatedVersionsTable,
} from "./components/policies";

// Re-export analytics components (selective exports for better tree-shaking)
export { DataSourceUsageAnalytics } from "./components/analytics";

// Re-export components table (selective exports for better tree-shaking)
export { ComponentsTable } from "./components/components";
