// Performance: Import React for lazy loading
import { lazy } from "react";

// Re-export essential utilities (selective exports for better tree-shaking)
export { parseDate, cn } from "./lib/utils";
// Note: Other utils from "./lib/utils" not currently used by apps
export * from "./lib/chart";

// Re-export API utilities (selective exports for better tree-shaking)
export {
    SharedResponseUtils,
    parseWorkflowRequest,
    parseQueryParams,
    getProjectIdFromParams,
    validateWorkflowSaveRequest,
    validateServerUrl,
    type SharedApiConfig,
} from "./lib/api/shared-response-utils";
export {
    type Configuration,
    type ApiClientConfig,
    createApiConfig,
    withErrorHandling,
} from "./lib/api/api-utils";

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
// Table components - using regular imports for better stability
export { DataTable } from "./components/data-table";
export { ResourceTable, DeletableResourceTable } from "./components/resource-table";
export { EnvironmentVariablesEditor } from "./components/environment-variables-editor";

// Lightweight components - keep regular exports
export { DetailsButton } from "./components/details-button";
export { ShortenedID } from "./components/shortened-id";

// Re-export types (not affected by lazy loading)
export type { EnvironmentVariablesEditorProps } from "./components/environment-variables-editor";
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
export { SharedNavbar, type NavigationSection } from "./components/navigation/shared-navbar";

// Re-export run components (selective exports for better tree-shaking)
export { RunsPage } from "./components/runs/runs-list-page";
export { RunPageContent, type RunPageConfig } from "./components/runs/run-page-content";
// Note: Run-related types (BaseRunNodeLayout, BaseRunNodeData, RunLogEvent, RunLog, RunLogs)
// not currently used by apps - RunLogs comes from @vulkanlabs/client-open instead

// Re-export workflow frame components
export * from "./components/app-workflow-frame";

// Re-export data source components (selective exports for better tree-shaking)
// Data source components - using regular imports to avoid lazy loading issues
export { CreateDataSourceDialog } from "./components/data-sources/create-data-source-dialog";
export { DataSourcesTable as SharedDataSourcesTable } from "./components/data-sources/data-sources-table";
export { DataSourceDetailPage } from "./components/data-sources/data-source-detail-page";

// Re-export types
export type { CreateDataSourceDialogConfig } from "./components/data-sources/create-data-source-dialog";
export type { DataSourceDetailPageConfig } from "./components/data-sources/data-source-detail-page";

// Re-export workflow components (selective exports for better tree-shaking)
// Heavy workflow components with lazy loading for better startup performance
export const WorkflowFrame = lazy(() =>
    import("./workflow").then((m) => ({ default: m.WorkflowFrame })),
);

// Lightweight API components - keep regular exports
export { WorkflowApiProvider, WorkflowDataProvider, createWorkflowApiClient } from "./workflow";

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
export { CreatePolicyDialog as SharedCreatePolicyDialog } from "./components/policies/create-policy-dialog";
export { CreatePolicyVersionDialog } from "./components/policies/create-policy-version-dialog";
export { PoliciesTable as SharedPoliciesTable } from "./components/policies/policies-table";
export { PolicyVersionsTable } from "./components/policies/policy-versions-table";
export { UpdateAllocationDialog } from "./components/policies/update-allocation-dialog";
export { SharedAllocatedVersionsTable } from "./components/policies/allocated-versions-table";

// Re-export analytics components (selective exports for better tree-shaking)
export { DataSourceUsageAnalytics } from "./components/analytics/usage-analytics";
// export { PolicyRunsChart, PolicyMetricsCard } from "./components/analytics/policy-metrics";

// Re-export components (selective exports for better tree-shaking)
export { ComponentsTable } from "./components/components/components-table";
export { CreateComponentDialog } from "./components/components/create-component-dialog";
export { ComponentsEnvTab } from "./components/components/components-env-tab";

// Re-export launcher components (selective exports for better tree-shaking)
export {
    PolicyLauncherPage,
    PolicyLauncherButton,
    type PolicyLauncherConfig,
    type PolicyLauncherPageConfig,
    type PolicyLauncherButtonConfig,
} from "./components/policy-versions/policy-launcher";

// Re-export resources components (selective exports for better tree-shaking)
export {
    PolicyResourcesEnvironmentVariables,
    PolicyResourcesDataSourcesTable,
    PolicyResourcesRequirementsEditor,
    type PolicyResourcesEnvironmentVariablesConfig,
    type PolicyResourcesDataSourcesTableConfig,
    type PolicyResourcesRequirementsEditorConfig,
} from "./components/policy-versions/policy-resources";

// Re-export policy metrics component (selective exports for better tree-shaking)
export {
    PolicyMetrics,
    type PolicyMetricsConfig,
} from "./components/policies/policy-metrics";
