"use client";

import React, { createContext, useContext, useMemo, type ReactNode } from "react";
import type { WorkflowApiClient, WorkflowApiClientConfig } from "./types";
import { createWorkflowApiClient } from "./client";

/**
 * React context for the workflow API client
 */
const WorkflowApiContext = createContext<WorkflowApiClient | null>(null);

/**
 * Props for the WorkflowApiProvider component
 */
export interface WorkflowApiProviderProps {
    children: ReactNode;
    client?: WorkflowApiClient;
    config?: WorkflowApiClientConfig;
}

/**
 * Provider component that supplies a WorkflowApiClient to child components
 *
 * @example
 * ```tsx
 * // Use with default client
 * <WorkflowApiProvider>
 *   <WorkflowComponents />
 * </WorkflowApiProvider>
 *
 * // Use with custom client
 * <WorkflowApiProvider client={customClient}>
 *   <WorkflowComponents />
 * </WorkflowApiProvider>
 *
 * // Use with configuration
 * <WorkflowApiProvider config={{ timeout: 60000 }}>
 *   <WorkflowComponents />
 * </WorkflowApiProvider>
 * ```
 */
export function WorkflowApiProvider({ children, client, config }: WorkflowApiProviderProps) {
    const apiClient = useMemo(() => {
        // Use provided client or create a default one
        return client || createWorkflowApiClient(config);
    }, [client, config]);

    return <WorkflowApiContext.Provider value={apiClient}>{children}</WorkflowApiContext.Provider>;
}

/**
 * Hook to access the workflow API client from context
 *
 * @throws {Error} If used outside of WorkflowApiProvider
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const api = useWorkflowApi();
 *
 *   const handleSave = async () => {
 *     const result = await api.saveWorkflowSpec(policyVersion, spec, uiMetadata);
 *     // Handle result...
 *   };
 * }
 * ```
 */
export function useWorkflowApi(): WorkflowApiClient {
    const client = useContext(WorkflowApiContext);

    if (!client) {
        throw new Error(
            "useWorkflowApi must be used within a WorkflowApiProvider. " +
                "Make sure to wrap your component tree with <WorkflowApiProvider>.",
        );
    }

    return client;
}
