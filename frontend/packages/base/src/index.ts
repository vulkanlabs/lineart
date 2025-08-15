// Performance: Import React for lazy loading
import { lazy } from "react";

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

// Re-export data source charts
export { 
    CacheHitRatioChart,
    ErrorRateChart,
    LoadingChartState,
    RequestVolumeChart,
    ResponseTimeChart,
} from "./components/charts/data-source-charts";

// Re-export policy charts
export {
    AvgDurationByStatusChart,
    RunDurationStatsChart,
    RunErrorRateChart,
    RunOutcomeDistributionChart,
    RunOutcomesChart,
    RunsChart,
} from "./components/charts/policy-stats";

// Re-export reusable components (selective exports for better tree-shaking)
// Performance: Heavy components with lazy loading for code splitting and reduced initial bundle size
export const DataTable = lazy(() => import("./components/data-table").then(m => ({ default: m.DataTable })));
export const ResourceTable = lazy(() => import("./components/resource-table").then(m => ({ default: m.ResourceTable })));
export const DeletableResourceTable = lazy(() => import("./components/resource-table").then(m => ({ default: m.DeletableResourceTable })));
export const EnvironmentVariablesEditor = lazy(() => import("./components/environment-variables-editor").then(m => ({ default: m.EnvironmentVariablesEditor })));

// Lightweight components - keep regular exports
export { DetailsButton } from "./components/details-button";
export { ShortenedID } from "./components/shortened-id";

// Re-export types (not affected by lazy loading)
export type { 
    EnvironmentVariablesEditorProps 
} from "./components/environment-variables-editor";
export type { 
    DeletableResourceTableProps,
    SearchFilterOptions,
    DeleteResourceOptions,
} from "./components/resource-table";
export { DeletableResourceTableActions } from "./components/resource-table";
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
// Heavy dialog components with lazy loading
export const SharedCreateDataSourceDialog = lazy(() => import("./components/data-sources").then(m => ({ default: m.SharedCreateDataSourceDialog })));
export const SharedDataSourcesTable = lazy(() => import("./components/data-sources").then(m => ({ default: m.DataSourcesTable })));

// Re-export types
export type { CreateDataSourceDialogConfig } from "./components/data-sources";

// Re-export workflow components (selective exports for better tree-shaking)
// Heavy workflow components with lazy loading for better startup performance
export const WorkflowFrame = lazy(() => import("./workflow").then(m => ({ default: m.WorkflowFrame })));

// Lightweight API components - keep regular exports
export { 
  WorkflowApiProvider,
  WorkflowDataProvider,
  createWorkflowApiClient,
} from "./workflow";

// Workflow utilities used by apps
export {
  defaultElkOptions,
  getLayoutedNodes,
  standardizeNodeName,
  createWorkflowState,
} from "./workflow";

// Workflow types used by apps
export type {
  NodeDependency,
  DataSource,
  VulkanNode,
  VulkanNodeData,
  WorkflowState,
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
