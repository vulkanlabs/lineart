"use client";

import React, {
    createContext,
    useContext,
    useEffect,
    useState,
    useMemo,
    type ReactNode,
} from "react";
import { useWorkflowApi } from "../api/context";
import type { DataSource } from "../api/types";
import type { PolicyVersion } from "@vulkanlabs/client-open";

/**
 * Shape of data provided by WorkflowDataProvider
 */
export interface WorkflowData {
    // Policy data
    policyVersions: PolicyVersion[];
    isPoliciesLoading: boolean;
    policiesError: string | null;

    // Data source data
    dataSources: DataSource[];
    isDataSourcesLoading: boolean;
    dataSourcesError: string | null;

    // Refresh functions
    refreshPolicies: () => Promise<void>;
    refreshDataSources: () => Promise<void>;
    refreshAll: () => Promise<void>;
}

/**
 * React context for workflow data
 */
const WorkflowDataContext = createContext<WorkflowData | null>(null);

/**
 * Props for the WorkflowDataProvider component
 */
export interface WorkflowDataProviderProps {
    children: ReactNode;
    /**
     * Whether to automatically fetch data on mount
     * @default true
     */
    autoFetch?: boolean;
    /**
     * Whether to include archived policy versions
     * @default false
     */
    includeArchived?: boolean;
    /**
     * Specific policy ID to filter by (optional)
     */
    policyId?: string | null;
    /**
     * Project ID to filter by (optional)
     */
    projectId?: string;
}

/**
 * Provider component that fetches and caches workflow-related data
 *
 * This provider:
 * - Uses the WorkflowApiClient to fetch data
 * - Manages loading states and errors
 * - Provides cached data to child components
 * - Offers refresh functions for manual data updates
 *
 * @example
 * ```tsx
 * <WorkflowApiProvider client={apiClient}>
 *   <WorkflowDataProvider>
 *     <WorkflowComponents />
 *   </WorkflowDataProvider>
 * </WorkflowApiProvider>
 * ```
 */
export function WorkflowDataProvider({
    children,
    autoFetch = true,
    includeArchived = false,
    policyId = null,
    projectId,
}: WorkflowDataProviderProps) {
    const apiClient = useWorkflowApi();

    // Policy versions state
    const [policyVersions, setPolicyVersions] = useState<PolicyVersion[]>([]);
    const [isPoliciesLoading, setIsPoliciesLoading] = useState(false);
    const [policiesError, setPoliciesError] = useState<string | null>(null);

    // Data sources state
    const [dataSources, setDataSources] = useState<DataSource[]>([]);
    const [isDataSourcesLoading, setIsDataSourcesLoading] = useState(false);
    const [dataSourcesError, setDataSourcesError] = useState<string | null>(null);

    // Fetch policy versions
    const fetchPolicyVersions = async () => {
        setIsPoliciesLoading(true);
        setPoliciesError(null);

        try {
            const versions = await apiClient.fetchPolicyVersions(
                policyId,
                includeArchived,
                projectId,
            );
            setPolicyVersions(versions);
        } catch (error) {
            const errorMessage =
                error instanceof Error ? error.message : "Failed to fetch policy versions";
            setPoliciesError(errorMessage);
            console.error("Error fetching policy versions:", error);
        } finally {
            setIsPoliciesLoading(false);
        }
    };

    // Fetch data sources
    const fetchDataSources = async () => {
        setIsDataSourcesLoading(true);
        setDataSourcesError(null);

        try {
            const sources = await apiClient.fetchDataSources(projectId);
            setDataSources(sources);
        } catch (error) {
            const errorMessage =
                error instanceof Error ? error.message : "Failed to fetch data sources";
            setDataSourcesError(errorMessage);
            console.error("Error fetching data sources:", error);
        } finally {
            setIsDataSourcesLoading(false);
        }
    };

    // Refresh functions
    const refreshPolicies = async () => {
        await fetchPolicyVersions();
    };

    const refreshDataSources = async () => {
        await fetchDataSources();
    };

    const refreshAll = async () => {
        await Promise.all([fetchPolicyVersions(), fetchDataSources()]);
    };

    // Auto-fetch on mount and when dependencies change
    useEffect(() => {
        if (autoFetch) {
            refreshAll();
        }
    }, [autoFetch, policyId, includeArchived, projectId]);

    // Memoize the context value to prevent unnecessary re-renders
    const value = useMemo<WorkflowData>(
        () => ({
            // Policy data
            policyVersions,
            isPoliciesLoading,
            policiesError,

            // Data source data
            dataSources,
            isDataSourcesLoading,
            dataSourcesError,

            // Refresh functions
            refreshPolicies,
            refreshDataSources,
            refreshAll,
        }),
        [
            policyVersions,
            isPoliciesLoading,
            policiesError,
            dataSources,
            isDataSourcesLoading,
            dataSourcesError,
            refreshPolicies,
            refreshDataSources,
            refreshAll,
        ],
    );

    return <WorkflowDataContext.Provider value={value}>{children}</WorkflowDataContext.Provider>;
}

/**
 * Hook to access workflow data from context
 *
 * @throws {Error} If used outside of WorkflowDataProvider
 *
 * @example
 * ```tsx
 * function PolicyNode() {
 *   const { policyVersions, isPoliciesLoading } = useWorkflowData();
 *
 *   if (isPoliciesLoading) return <div>Loading...</div>;
 *
 *   return (
 *     <select>
 *       {policyVersions.map(version => (
 *         <option key={version.policy_version_id} value={version.policy_version_id}>
 *           {version.alias}
 *         </option>
 *       ))}
 *     </select>
 *   );
 * }
 * ```
 */
export function useWorkflowData(): WorkflowData {
    const data = useContext(WorkflowDataContext);

    if (!data) {
        throw new Error(
            "useWorkflowData must be used within a WorkflowDataProvider. " +
                "Make sure to wrap your component tree with <WorkflowDataProvider>.",
        );
    }

    return data;
}
