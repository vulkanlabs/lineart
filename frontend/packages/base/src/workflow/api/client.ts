import type {
    PolicyVersion,
    PolicyDefinitionDict,
    UIMetadata,
    Component,
} from "@vulkanlabs/client-open";

import type {
    WorkflowApiClient,
    SaveWorkflowResult,
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
    ): Promise<SaveWorkflowResult> {
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
                // Consolidate all error parsing logic here
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

                if (result) {
                    // Extract error message from various possible formats
                    if (typeof result.error === "string") errorMessage = result.error;
                    else if (typeof result.error === "object" && result.error)
                        errorMessage =
                            result.error.message ||
                            result.error.detail ||
                            JSON.stringify(result.error);
                    else if (result.message) errorMessage = result.message;
                    else if (result.detail) errorMessage = result.detail;

                    // Handle [object Object] case from server
                    if (
                        errorMessage === "[object Object]" ||
                        errorMessage.includes("[object Object]")
                    )
                        errorMessage = "Internal server error";
                }

                return {
                    success: false,
                    error: errorMessage,
                    data: null,
                };
            }

            // Return the result as-is for successful responses
            return {
                success: true,
                error: null,
                data: result,
                ...result,
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
    ): Promise<PolicyVersion[]> {
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
            return data;
        } catch (error) {
            console.error("Error fetching policy versions:", error);
            throw new Error(
                error instanceof Error ? error.message : "Failed to fetch policy versions",
            );
        }
    }

    /**
     * Fetch available data sources using the API route
     */
    async fetchDataSources(projectId?: string): Promise<DataSource[]> {
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
            return data;
        } catch (error) {
            console.error("Error fetching data sources:", error);
            throw new Error(
                error instanceof Error ? error.message : "Failed to fetch data sources",
            );
        }
    }

    /**
     * Fetch available components using the API route
     */
    async fetchComponents(includeArchived = false, projectId?: string): Promise<Component[]> {
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
            return data;
        } catch (error) {
            console.error("Error fetching components:", error);
            throw new Error(error instanceof Error ? error.message : "Failed to fetch components");
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
