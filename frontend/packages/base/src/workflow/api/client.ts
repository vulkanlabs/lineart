import type {
    PolicyVersion,
    PolicyDefinitionDict,
    UIMetadata,
    Component,
} from "@vulkanlabs/client-open";

import type {
    WorkflowApiClient,
    ApiResult,
    WorkflowApiClientConfig,
    DataSource,
    Workflow,
} from "./types";

/**
 * Default implementation of WorkflowApiClient that uses API routes
 * This client assumes the API routes are available at /api/workflow/*
 */
export class DefaultWorkflowApiClient implements WorkflowApiClient {
    private config: WorkflowApiClientConfig;

    constructor(config: WorkflowApiClientConfig = {}) {
        this.config = {
            baseUrl: "",
            timeout: 30000,
            ...config,
        };
    }

    /**
     * Save a workflow specification using the API route
     */
    async saveWorkflowSpec(
        workflow: Workflow,
        spec: PolicyDefinitionDict,
        uiMetadata: { [key: string]: UIMetadata },
        projectId?: string,
    ): Promise<ApiResult<any>> {
        try {
            const params = new URLSearchParams();

            if (projectId) {
                params.append("project_id", projectId);
            }

            const queryString = params.toString();
            const url = `${this.config.baseUrl}/api/workflow/save${queryString ? `?${queryString}` : ""}`;

            const response = await fetch(url, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    ...this.config.headers,
                },
                body: JSON.stringify({ workflow, spec, uiMetadata }),
                signal: this.createTimeoutSignal(),
            });

            let result;
            try {
                result = await response.json();
            } catch (parseError) {
                result = null;
            }

            // Check if the HTTP response indicates an error
            if (!response.ok) {
                const errorMessage = result?.error
                    ? (typeof result.error === "string" ? result.error : JSON.stringify(result.error))
                    : `HTTP ${response.status}: ${response.statusText}`;

                return {
                    success: false,
                    error: errorMessage,
                    data: null,
                };
            }

            // Return successful response
            return {
                success: true,
                error: null,
                data: result,
            };
        } catch (error) {
            console.error("Error saving workflow:", error);
            return {
                success: false,
                error: error instanceof Error ? error.message : "Unknown error occurred",
                data: null,
            };
        }
    }

    /**
     * Fetch policy versions using the API route
     */
    async fetchPolicyVersions(
        policyId?: string | null,
        includeArchived = false,
        projectId?: string,
    ): Promise<ApiResult<PolicyVersion[]>> {
        try {
            const params = new URLSearchParams({
                include_archived: includeArchived.toString(),
            });

            if (policyId) {
                params.append("policy_id", policyId);
            }

            if (projectId) {
                params.append("project_id", projectId);
            }

            const response = await fetch(
                `${this.config.baseUrl}/api/workflow/policy-versions?${params}`,
                {
                    headers: this.config.headers,
                    signal: this.createTimeoutSignal(),
                },
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data: PolicyVersion[] = await response.json();
            return {
                success: true,
                error: null,
                data,
            };
        } catch (error) {
            console.error("Error fetching policy versions:", error);
            return {
                success: false,
                error: error instanceof Error ? error.message : "Failed to fetch policy versions",
                data: null,
            };
        }
    }

    /**
     * Fetch available data sources using the API route
     */
    async fetchDataSources(projectId?: string): Promise<ApiResult<DataSource[]>> {
        try {
            const params = new URLSearchParams();

            if (projectId) {
                params.append("project_id", projectId);
            }

            const queryString = params.toString();
            const url = `${this.config.baseUrl}/api/workflow/data-sources${queryString ? `?${queryString}` : ""}`;

            const response = await fetch(url, {
                headers: this.config.headers,
                signal: this.createTimeoutSignal(),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data: DataSource[] = await response.json();
            return {
                success: true,
                error: null,
                data,
            };
        } catch (error) {
            console.error("Error fetching data sources:", error);
            return {
                success: false,
                error: error instanceof Error ? error.message : "Failed to fetch data sources",
                data: null,
            };
        }
    }

    /**
     * Fetch available components using the API route
     */
    async fetchComponents(
        includeArchived = false,
        projectId?: string,
    ): Promise<ApiResult<Component[]>> {
        try {
            const params = new URLSearchParams({
                include_archived: includeArchived.toString(),
            });

            if (projectId) {
                params.append("project_id", projectId);
            }

            const response = await fetch(
                `${this.config.baseUrl}/api/workflow/components?${params}`,
                {
                    headers: this.config.headers,
                    signal: this.createTimeoutSignal(),
                },
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data: Component[] = await response.json();
            return {
                success: true,
                error: null,
                data,
            };
        } catch (error) {
            console.error("Error fetching components:", error);
            return {
                success: false,
                error: error instanceof Error ? error.message : "Failed to fetch components",
                data: null,
            };
        }
    }

    /**
     * Create an AbortSignal for request timeout
     */
    private createTimeoutSignal(): AbortSignal | undefined {
        if (!this.config.timeout) return undefined;

        const controller = new AbortController();
        setTimeout(() => controller.abort(), this.config.timeout);
        return controller.signal;
    }
}

/**
 * Factory function to create a default workflow API client
 */
export function createWorkflowApiClient(config?: WorkflowApiClientConfig): WorkflowApiClient {
    return new DefaultWorkflowApiClient(config);
}
