import { formatISO, parseISO } from "date-fns";
import { Configuration } from "@vulkanlabs/client-open";

/**
 * Configuration options for creating API clients
 */
export interface ApiClientConfig {
  /** Base URL for the API server */
  baseUrl: string;
  /** Optional default headers to include with all requests */
  headers?: Record<string, string>;
  /** Optional request timeout in milliseconds */
  timeout?: number;
  /** Optional credentials setting for CORS requests */
  credentials?: RequestCredentials;
}

/**
 * Creates a standardized Configuration object for auto-generated API clients
 *
 * @param config - API client configuration options
 * @returns Configuration object ready for use with generated API clients
 *
 * @example
 * ```typescript
 * import { PoliciesApi } from '@vulkanlabs/client-open'
 * import { createApiConfig } from '@vulkanlabs/api-utils'
 *
 * const config = createApiConfig({
 *   baseUrl: 'https://api.vulkan.com',
 *   headers: { 'Authorization': 'Bearer token' }
 * })
 *
 * const policiesApi = new PoliciesApi(config)
 * ```
 */
export const createApiConfig = (config: ApiClientConfig): Configuration => {
  return new Configuration({
    basePath: config.baseUrl,
    headers: config.headers,
    credentials: config.credentials,
    // Note: timeout is not directly supported by the generated Configuration class
    // but can be handled at the fetch level if needed
  });
};

/**
 * Wraps API operations with consistent error handling and context information
 *
 * @param operation - Promise representing the API operation
 * @param context - Descriptive context for what operation is being performed
 * @returns Promise with enhanced error messages
 *
 * @example
 * ```typescript
 * const policies = await withErrorHandling(
 *   policiesApi.listPolicies({ includeArchived: false }),
 *   'fetch policies'
 * )
 * ```
 */
export const withErrorHandling = async <T>(
  operation: Promise<T>,
  context: string,
): Promise<T> => {
  try {
    return await operation;
  } catch (error) {
    // Extract meaningful error message
    let message: string;
    if (error instanceof Error) {
      message = error.message;
    } else if (typeof error === "string") {
      message = error;
    } else {
      message = "Unknown error occurred";
    }

    // Create enhanced error with context
    const enhancedError = new Error(`Failed to ${context}: ${message}`);

    // Preserve original error as cause if possible
    if (error instanceof Error) {
      (enhancedError as any).cause = error;
    }

    throw enhancedError;
  }
};

/**
 * Collection of utility functions for common API operations
 */
export const apiHelpers = {
  /**
   * Formats a Date object to ISO date string (YYYY-MM-DD format)
   * Useful for API endpoints that expect date parameters
   */
  formatDate: (date: Date): string => {
    return formatISO(date, { representation: "date" });
  },

  /**
   * Formats a Date object to ISO datetime string
   * Useful for API endpoints that expect full datetime parameters
   */
  formatDateTime: (date: Date): string => {
    return formatISO(date);
  },

  /**
   * Parses an ISO date string back to a Date object
   * Useful for processing API responses with date fields
   */
  parseDate: (dateString: string): Date => {
    return parseISO(dateString);
  },

  /**
   * Creates URLSearchParams from an object, filtering out null/undefined values
   * Useful for building query parameters for API requests
   */
  createQueryParams: (params: Record<string, any>): URLSearchParams => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    return searchParams;
  },

  /**
   * Converts a file to base64 string for API upload operations
   */
  fileToBase64: (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        // Remove data:mime;base64, prefix
        const parts = result.split(",");
        const base64: string = parts.length > 1 ? parts[1]! : "";
        resolve(base64);
      };
      reader.onerror = (error) => reject(error);
    });
  },
};

/**
 * Common HTTP status codes for API responses
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
} as const;

/**
 * Type-safe hook-style API utilities for React components
 * This provides a consistent pattern for using APIs in React applications
 */
export const createApiHook = <TParams, TResult>(
  apiCall: (params: TParams) => Promise<TResult>,
) => {
  return (params: TParams, context: string) => {
    const execute = (): Promise<TResult> => {
      return withErrorHandling(apiCall(params), context);
    };

    return { execute };
  };
};

// Re-export Configuration type for convenience
export type { Configuration } from "@vulkanlabs/client-open";
