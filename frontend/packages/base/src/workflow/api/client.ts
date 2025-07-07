import type { PolicyVersion, PolicyDefinitionDictInput, UIMetadata } from "@vulkan/client-open";

import type {
    WorkflowApiClient,
    SaveWorkflowResult,
    WorkflowApiClientConfig,
    DataSource,
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
        policyVersion: PolicyVersion,
        spec: PolicyDefinitionDictInput,
        uiMetadata: { [key: string]: UIMetadata },
    ): Promise<SaveWorkflowResult> {
        try {
            const response = await fetch(`${this.config.baseUrl}/api/workflow/save`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    ...this.config.headers,
                },
                body: JSON.stringify({ policyVersion, spec, uiMetadata }),
                signal: this.createTimeoutSignal(),
            });

            const result = await response.json();
            return result;
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
    ): Promise<PolicyVersion[]> {
        try {
            const params = new URLSearchParams({
                include_archived: includeArchived.toString(),
            });

            if (policyId) {
                params.append("policy_id", policyId);
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
    async fetchDataSources(): Promise<DataSource[]> {
        try {
            const response = await fetch(`${this.config.baseUrl}/api/workflow/data-sources`, {
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
