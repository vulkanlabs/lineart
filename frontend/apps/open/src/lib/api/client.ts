import "server-only";

import {
    ComponentsApi,
    DataSourcesApi,
    PoliciesApi,
    PolicyVersionsApi,
    RunsApi,
    Configuration,
} from "@vulkanlabs/client-open";

const apiConfig = new Configuration({
    basePath: process.env.VULKAN_SERVER_URL!,
    headers: {
        "Content-Type": "application/json",
    },
});

export const componentsApi = new ComponentsApi(apiConfig);
export const dataSourcesApi = new DataSourcesApi(apiConfig);
export const policiesApi = new PoliciesApi(apiConfig);
export const policyVersionsApi = new PolicyVersionsApi(apiConfig);
export const runsApi = new RunsApi(apiConfig);

/**
 * Wraps API operations with consistent error handling and context
 * @param operation - The async operation to execute
 * @param context - Description of the operation for error messages
 * @returns Promise that resolves with the operation result or throws enhanced error
 * @throws Error with contextual information about the failure
 * @example
 * ```typescript
 * const result = await withErrorHandling(
 *   apiClient.getData(),
 *   'fetch user data'
 * );
 * // If it fails, throws: "Failed to fetch user data: <original error>"
 * ```
 */
export const withErrorHandling = async <T>(operation: Promise<T>, context: string): Promise<T> => {
    try {
        return await operation;
    } catch (error) {
        let message: string;
        if (error instanceof Error) message = error.message;
        else if (typeof error === "string") message = error;
        else message = "Unknown error occurred";

        const enhancedError = new Error(`Failed to ${context}: ${message}`);

        if (error instanceof Error) (enhancedError as any).cause = error;
        throw enhancedError;
    }
};

// Re-export common types
export type { DateRange } from "./types";
