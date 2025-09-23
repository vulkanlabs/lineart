import type {
    PolicyVersion,
    PolicyDefinitionDict,
    UIMetadata,
    Component,
    DataSource,
} from "@vulkanlabs/client-open";

import type { WorkflowApiClient, ApiResult } from "./types";

/**
 * Mock implementation of WorkflowApiClient for testing and development
 *
 * This client simulates API responses without making actual network requests.
 * Useful for:
 * - Unit testing
 * - Development when backend is not available
 * - Storybook stories
 * - Component demos
 */
export class MockWorkflowApiClient implements WorkflowApiClient {
    private delay: number;
    private shouldFail: boolean;

    constructor(options: { delay?: number; shouldFail?: boolean } = {}) {
        this.delay = options.delay ?? 1000;
        this.shouldFail = options.shouldFail ?? false;
    }

    async fetchComponents(
        includeArchived?: boolean,
        projectId?: string,
    ): Promise<ApiResult<Component[]>> {
        // Simulate network delay
        await this.simulateDelay();

        if (this.shouldFail) {
            return {
                success: false,
                error: "Mock API client configured to fail",
                data: null,
            };
        }

        return {
            success: true,
            data: [],
            error: null,
        };
    }

    /**
     * Mock save workflow specification
     */
    async saveWorkflowSpec(
        policyVersion: PolicyVersion,
        spec: PolicyDefinitionDict,
        uiMetadata: { [key: string]: UIMetadata },
        projectId?: string,
    ): Promise<ApiResult<any>> {
        // Simulate network delay
        await this.simulateDelay();

        if (this.shouldFail) {
            return {
                success: false,
                error: "Mock API client configured to fail",
                data: null,
            };
        }

        // Simulate successful save
        console.log("Mock API: Saving workflow spec", {
            policyVersion,
            spec,
            uiMetadata,
            projectId,
        });

        return {
            success: true,
            error: null,
            data: {
                id: policyVersion.policy_version_id,
                updatedAt: new Date().toISOString(),
                version: Math.floor(Math.random() * 1000),
            },
        };
    }

    /**
     * Mock fetch policy versions
     */
    async fetchPolicyVersions(
        policyId?: string | null,
        includeArchived = false,
        projectId?: string,
    ): Promise<ApiResult<PolicyVersion[]>> {
        // Simulate network delay
        await this.simulateDelay();

        if (this.shouldFail) {
            return {
                success: false,
                error: "Mock API client configured to fail",
                data: null,
            };
        }

        console.log("Mock API: Fetching policy versions", { policyId, includeArchived, projectId });

        // Return mock data
        const mockPolicyVersions: PolicyVersion[] = [
            {
                policy_version_id: "mock-version-1",
                policy_id: policyId || "mock-policy-1",
                alias: "Mock Version 1",
                workflow: {
                    workflow_id: "mock-workflow-1",
                    spec: {
                        nodes: [],
                        input_schema: {},
                    },
                    requirements: [],
                    ui_metadata: {},
                    status: "VALID" as any,
                },
                created_at: new Date(),
                last_updated_at: new Date(),
                archived: false,
            },
            {
                policy_version_id: "mock-version-2",
                policy_id: policyId || "mock-policy-1",
                alias: "Mock Version 2",
                workflow: {
                    workflow_id: "mock-workflow-2",
                    spec: {
                        nodes: [],
                        input_schema: {},
                    },
                    requirements: [],
                    ui_metadata: {},
                    status: "VALID" as any,
                },
                created_at: new Date(),
                last_updated_at: new Date(),
                archived: includeArchived,
            },
        ];

        const filteredVersions = includeArchived
            ? mockPolicyVersions
            : mockPolicyVersions.filter((v) => !v.archived);

        return {
            success: true,
            data: filteredVersions,
            error: null,
        };
    }

    /**
     * Mock fetch data sources
     */
    async fetchDataSources(projectId?: string): Promise<ApiResult<DataSource[]>> {
        // Simulate network delay
        await this.simulateDelay();

        if (this.shouldFail) {
            return {
                success: false,
                error: "Mock API client configured to fail",
                data: null,
            };
        }

        console.log("Mock API: Fetching data sources", { projectId });

        // Return mock data sources
        const mockDataSources: DataSource[] = [
            {
                name: "Mock Source 1",
                data_source_id: "mock-source-1",
                source: { url: "https://example.com/data", path: "", file_id: "" },
                archived: false,
                created_at: new Date(),
                last_updated_at: new Date(),
            },
        ];

        return {
            success: true,
            data: mockDataSources,
            error: null,
        };
    }

    /**
     * Simulate network delay
     */
    private async simulateDelay(): Promise<void> {
        if (this.delay > 0) {
            await new Promise((resolve) => setTimeout(resolve, this.delay));
        }
    }

    /**
     * Configure the mock to succeed or fail
     */
    setShouldFail(shouldFail: boolean): void {
        this.shouldFail = shouldFail;
    }

    /**
     * Configure the simulated delay
     */
    setDelay(delay: number): void {
        this.delay = delay;
    }
}

/**
 * Factory function to create a mock workflow API client
 */
export function createMockWorkflowApiClient(options?: {
    delay?: number;
    shouldFail?: boolean;
}): WorkflowApiClient {
    return new MockWorkflowApiClient(options);
}
