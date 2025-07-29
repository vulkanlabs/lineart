import type {
    PolicyVersion,
    PolicyDefinitionDictInput,
    UIMetadata,
    Component,
} from "@vulkanlabs/client-open";

/**
 * Result type for save operations
 */
export interface SaveWorkflowResult {
    success: boolean;
    error: string | null;
    data: any;
}

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
 */
export interface WorkflowApiClient {
    /**
     * Save a workflow specification to the server
     */
    saveWorkflowSpec(
        workflow: Workflow,
        spec: PolicyDefinitionDictInput,
        uiMetadata: { [key: string]: UIMetadata },
        projectId?: string,
    ): Promise<SaveWorkflowResult>;

    /**
     * Fetch policy versions from the server
     */
    fetchPolicyVersions(
        policyId?: string | null,
        includeArchived?: boolean,
        projectId?: string,
    ): Promise<PolicyVersion[]>;

    /**
     * Fetch available data sources from the server
     */
    fetchDataSources(projectId?: string): Promise<DataSource[]>;
}

/**
 * Configuration options for the workflow API client
 */
export interface WorkflowApiClientConfig {
    baseUrl?: string;
    timeout?: number;
    headers?: Record<string, string>;
}
