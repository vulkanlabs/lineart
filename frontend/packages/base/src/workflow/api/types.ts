import type {
    PolicyVersion,
    PolicyDefinitionDict,
    UIMetadata,
    Component,
    DataSource,
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
 * Interface defining the workflow API client contract
 * This abstraction allows different implementations (API routes, direct calls, mocks, etc.)
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

    /**
     * Fetch available components from the server
     */
    fetchComponents(includeArchived?: boolean, projectId?: string): Promise<Component[]>;
}

/**
 * Configuration options for the workflow API client
 */
export interface WorkflowApiClientConfig {
    baseUrl?: string;
    timeout?: number;
    headers?: Record<string, string>;
}
