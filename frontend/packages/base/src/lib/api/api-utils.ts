import { Configuration } from "@vulkanlabs/client-open";

/**
 * Configuration interface for API client setup
 * @example
 * ```typescript
 * const config: ApiClientConfig = {
 *   baseUrl: 'https://api.example.com',
 *   headers: { 'Authorization': 'Bearer token' },
 *   credentials: 'include'
 * };
 * ```
 */
export interface ApiClientConfig {
    /** Base URL for the API endpoints */
    baseUrl: string;
    /** Optional headers to include with requests */
    headers?: Record<string, string>;
    /** Request credentials mode for CORS */
    credentials?: RequestCredentials;
}

/**
 * Creates a Configuration object for the Vulkan Labs client
 * @param config - The API client configuration
 * @returns Configuration instance ready for use with API clients
 * @example
 * ```typescript
 * const config = createApiConfig({
 *   baseUrl: 'https://api.example.com',
 *   headers: { 'Content-Type': 'application/json' }
 * });
 * const apiClient = new SomeApi(config);
 * ```
 */
export const createApiConfig = (config: ApiClientConfig): Configuration => {
    return new Configuration({
        basePath: config.baseUrl,
        headers: config.headers,
        credentials: config.credentials,
    });
};

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

// Re-export Configuration type for convenience
export type { Configuration } from "@vulkanlabs/client-open";
