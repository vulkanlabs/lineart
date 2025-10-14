// @vulkanlabs/base - Main entry point
// Re-exports the most commonly used components and utilities

// === Core Utilities ===
export { parseDate, cn } from "./lib/utils";
export * from "./lib/chart";

// === API Utilities ===
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

// === Essential UI Components ===
// Most commonly used UI primitives
export { Button } from "./components/ui/button";
export {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "./components/ui/card";
export { Input } from "./components/ui/input";
export { Label } from "./components/ui/label";
export {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "./components/ui/dialog";
export { Badge } from "./components/ui/badge";
export { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./components/ui/tooltip";

// === Layout Components ===
export * from "./components/navigation";

// === Data Components ===
export { DataTable } from "./components/data-table";
export {
    ResourceTable,
    DeletableResourceTable,
    DeletableResourceTableActions,
} from "./components/resource-table";
export type {
    DeletableResourceTableProps,
    SearchFilterOptions,
    DeleteResourceOptions,
    ResourceReference,
    DisplayOptions,
} from "./components/resource-table";

// === Common Components ===
export { VulkanLogo, type VulkanLogoConfig } from "./components/logo";
export { DetailsButton } from "./components/details-button";
export { ShortenedID } from "./components/shortened-id";
export { RefreshButton } from "./components/refresh-button";
export {
    EnvironmentVariablesEditor,
    type EnvironmentVariablesEditorProps,
} from "./components/environment-variables-editor";
export {
    AutoSaveToggle,
    type AutoSaveState,
    type AutoSaveToggleProps,
} from "./components/auto-save-toggle";
export { NavigationGuard } from "./components/navigation-guard";

// === Animations ===
export * from "./components/animations";

// === Charts ===
export * from "./components/charts";

// === App Frame ===
export * from "./components/app-workflow-frame";

// === Workflow (Lazy Loaded) ===
// WorkflowFrame is exported as lazy-loaded for performance
import { lazy } from "react";
export const WorkflowFrame = lazy(() =>
    import("./workflow").then((m) => ({ default: m.WorkflowFrame })),
);

// Lightweight workflow components and utilities
export {
    WorkflowApiProvider,
    WorkflowDataProvider,
    createWorkflowApiClient,
    defaultElkOptions,
    getLayoutedNodes,
    standardizeNodeName,
    createWorkflowState,
} from "./workflow";

export type { NodeDependency, VulkanNode, VulkanNodeData, WorkflowState } from "./workflow";

// Re-export toast system
export { ToastProvider, ToastContainer, useToast, createGlobalToast } from "./components/toast";
export type { Toast } from "./components/toast";

// === Feature-specific Components ===
// For specific features, consumers should import from dedicated entry points:
// import { CreateDataSourceDialog } from "@vulkanlabs/base/components/data-sources"
// import { CreatePolicyDialog } from "@vulkanlabs/base/components/policies"
// import { Button, Card } from "@vulkanlabs/base/components/ui"
// import { WorkflowCanvas } from "@vulkanlabs/base/workflow"
