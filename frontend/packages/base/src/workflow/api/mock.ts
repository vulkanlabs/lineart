import type { PolicyVersion, PolicyDefinitionDictInput, UIMetadata } from "@vulkanlabs/client-open";

import type { WorkflowApiClient, SaveWorkflowResult, DataSource } from "./types";

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

    /**
     * Mock save workflow specification
     */
    async saveWorkflowSpec(
        policyVersion: PolicyVersion,
        spec: PolicyDefinitionDictInput,
        uiMetadata: { [key: string]: UIMetadata },
    ): Promise<SaveWorkflowResult> {
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
        console.log("Mock API: Saving workflow spec", { policyVersion, spec, uiMetadata });

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
    ): Promise<PolicyVersion[]> {
        // Simulate network delay
        await this.simulateDelay();

        if (this.shouldFail) {
            throw new Error("Mock API client configured to fail");
        }

        console.log("Mock API: Fetching policy versions", { policyId, includeArchived });

        // Return mock data
        const mockPolicyVersions: PolicyVersion[] = [
            {
                policy_version_id: "mock-version-1",
                policy_id: policyId || "mock-policy-1",
                alias: "Mock Version 1",
                spec: {
                    nodes: [],
                    input_schema: {},
                },
                requirements: [],
                ui_metadata: {},
                created_at: new Date(),
                last_updated_at: new Date(),
                status: "VALID" as any,
                archived: false,
            },
            {
                policy_version_id: "mock-version-2",
                policy_id: policyId || "mock-policy-1",
                alias: "Mock Version 2",
                spec: {
                    nodes: [],
                    input_schema: {},
                },
                requirements: [],
                ui_metadata: {},
                created_at: new Date(),
                last_updated_at: new Date(),
                status: "VALID" as any,
                archived: includeArchived,
            },
        ];

        return includeArchived ? mockPolicyVersions : mockPolicyVersions.filter((v) => !v.archived);
    }

    /**
     * Mock fetch data sources
     */
    async fetchDataSources(): Promise<DataSource[]> {
        // Simulate network delay
        await this.simulateDelay();

        if (this.shouldFail) {
            throw new Error("Mock API client configured to fail");
        }

        console.log("Mock API: Fetching data sources");

        // Return mock data sources
        const mockDataSources: DataSource[] = [
            {
                data_source_id: "mock-data-source-1",
                name: "Mock CSV Source",
                runtime_params: ["file_path", "delimiter"],
            },
            {
                data_source_id: "mock-data-source-2",
                name: "Mock Database Source",
                runtime_params: ["connection_string", "query"],
            },
            {
                data_source_id: "mock-data-source-3",
                name: "Mock API Source",
                runtime_params: ["endpoint", "api_key"],
            },
        ];

        return mockDataSources;
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
