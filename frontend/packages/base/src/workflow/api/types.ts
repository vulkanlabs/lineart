import type {
    PolicyVersion,
    PolicyDefinitionDict,
    UIMetadata,
    Component,
} from "@vulkanlabs/client-open";

/**
 * API result type for all API operations
 * Provides error handling and type safety
 */
export interface ApiResult<T> {
    success: boolean;
    data: T | null;
    error: string | null;
}

/**
 * Result type for save operations
 * @deprecated Use ApiResult<any>
 */
export interface SaveWorkflowResult extends ApiResult<any> {}

export type Workflow = PolicyVersion | Component;

/**
 * Data source type for workflow components
 * TODO: Import from @vulkanlabs/client-open when available
 */
export interface DataSource {
    data_source_id: string;
    name: string;
    runtime_params: string[];
}

/**
 * Interface defining the workflow API client contract
 * This abstraction allows different implementations (API routes, direct calls, mocks, etc.)
 * All methods return ApiResult<T> for error handling
 */
export interface WorkflowApiClient {
    /**
     * Save a workflow specification to the server
     */
    saveWorkflowSpec(
        workflow: Workflow,
        spec: PolicyDefinitionDict,
        uiMetadata: { [key: string]: UIMetadata },
        projectId?: string,
    ): Promise<ApiResult<any>>;

    /**
     * Fetch policy versions from the server
     */
    fetchPolicyVersions(
        policyId?: string | null,
        includeArchived?: boolean,
        projectId?: string,
    ): Promise<ApiResult<PolicyVersion[]>>;

    /**
     * Fetch available data sources from the server
     */
    fetchDataSources(projectId?: string): Promise<ApiResult<DataSource[]>>;

    /**
     * Fetch available components from the server
     */
    fetchComponents(includeArchived?: boolean, projectId?: string): Promise<ApiResult<Component[]>>;
}

/**
 * Configuration options for the workflow API client
 */
export interface WorkflowApiClientConfig {
    baseUrl?: string;
    timeout?: number;
    headers?: Record<string, string>;
}
