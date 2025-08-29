import { Configuration } from "@vulkanlabs/client-open";

export interface ApiClientConfig {
  baseUrl: string;
  headers?: Record<string, string>;
  timeout?: number;
  credentials?: RequestCredentials;
}

export const createApiConfig = (config: ApiClientConfig): Configuration => {
  return new Configuration({
    basePath: config.baseUrl,
    headers: config.headers,
    credentials: config.credentials,
  });
};

export const withErrorHandling = async <T>(
  operation: Promise<T>,
  context: string,
): Promise<T> => {
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