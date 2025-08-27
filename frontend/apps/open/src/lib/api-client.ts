"use client";

import { type ComponentBase } from "@vulkanlabs/client-open";
import { DataSourceSpec } from "@vulkanlabs/client-open";
import { Policy, PolicyCreate } from "@vulkanlabs/client-open";
import { Run } from "@vulkanlabs/client-open";

// Types

interface DateRange {
    from: Date;
    to: Date;
}

interface MetricsData {
    runsCount: any[];
    errorRate: any[];
    runDurationStats: any[];
    runDurationByStatus: any[];
}

interface RunOutcomes {
    runOutcomes: any[];
}

interface RunsResponse {
    runs: Run[] | null;
}

interface DataSourceUsage {
    usage: any[];
}

interface DataSourceMetrics {
    metrics: any[];
}

interface DataSourceCacheStats {
    cacheStats: any;
}

// Error Handling

/**
 * Custom error with additional context
 */
class ApiError extends Error {
    constructor(
        message: string,
        public status?: number,
        public originalError?: unknown,
    ) {
        super(message);
        this.name = "ApiError";
    }
}

// API Utilities

/**
 * Centralized fetch with consistent error handling and logging
 * Handles authentication, error parsing, and  etc
 *
 * @param url - The API endpoint to call
 * @param options - Fetch options (method, body, headers, etc.)
 * @returns Parsed JSON response data
 */
async function apiFetch<T>(url: string, options: RequestInit = {}): Promise<T> {
    const defaultHeaders = {
        "Content-Type": "application/json",
    };

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
        });

        // Parse error responses before throwing
        if (!response.ok) {
            const errorText = await response.text();
            const errorMessage = errorText || `HTTP ${response.status}: ${response.statusText}`;

            console.error(`API Error [${response.status}] ${url}:`, errorMessage);
            throw new ApiError(errorMessage, response.status);
        }

        return await response.json();
    } catch (error) {
        if (error instanceof ApiError) throw error;

        // Handle network and other fetch errors
        const message = `Network error calling ${url}: ${error instanceof Error ? error.message : "Unknown error"}`;
        console.error(message, error);
        throw new ApiError(message, undefined, error);
    }
}

// Policy Metrics

/**
 * Fetches details from  policy metrics
 *
 * @param policyId
 * @param dateRange - Time period for metrics
 * @param versions - List of policy version id's
 * @returns Metrics data with fallback to empty arrays on error
 */
export async function fetchPolicyMetrics({
    policyId,
    dateRange,
    versions,
}: {
    policyId: string;
    dateRange: DateRange;
    versions: string[];
}): Promise<MetricsData> {
    try {
        const data = await apiFetch<MetricsData>("/api/metrics", {
            method: "POST",
            body: JSON.stringify({ policyId, dateRange, versions }),
        });

        return {
            runsCount: Array.isArray(data.runsCount) ? data.runsCount : [],
            errorRate: Array.isArray(data.errorRate) ? data.errorRate : [],
            runDurationStats: Array.isArray(data.runDurationStats) ? data.runDurationStats : [],
            runDurationByStatus: Array.isArray(data.runDurationByStatus)
                ? data.runDurationByStatus
                : [],
        };
    } catch (error) {
        console.error("Failed to load policy metrics:", error);
        return {
            runsCount: [],
            errorRate: [],
            runDurationStats: [],
            runDurationByStatus: [],
        };
    }
}

/**
 * Fetches policy run success/failure analysis
 *
 * @param policyId - Policy to analyze
 * @param dateRange - Time range for outcome data
 * @param versions - Policy versions to include
 * @returns Run outcomes data for charting and analysis
 */
export async function fetchRunOutcomes({
    policyId,
    dateRange,
    versions,
}: {
    policyId: string;
    dateRange: DateRange;
    versions: string[];
}): Promise<RunOutcomes> {
    try {
        const data = await apiFetch<RunOutcomes>("/api/run-outcomes", {
            method: "POST",
            body: JSON.stringify({ policyId, dateRange, versions }),
        });

        return {
            runOutcomes: Array.isArray(data.runOutcomes) ? data.runOutcomes : [],
        };
    } catch (error) {
        console.error("Failed to load run outcomes:", error);
        return { runOutcomes: [] };
    }
}

// Runs

/**
 * Fetches all runs with a policy
 *
 * @param resourceId - Policy id to fetch runs
 * @param dateRange - Date filter
 * @returns List of runs or null
 */
export async function fetchRunsByPolicy({
    resourceId,
    dateRange,
}: {
    resourceId: string;
    dateRange: DateRange;
}): Promise<RunsResponse> {
    try {
        const data = await apiFetch<RunsResponse>("/api/runs", {
            method: "POST",
            body: JSON.stringify({ type: "policy", resourceId, dateRange }),
        });

        return { runs: data.runs || null };
    } catch (error) {
        console.error("Failed to load policy runs:", error);
        return { runs: null };
    }
}

/**
 * Fetches runs by policyVersion
 *
 * @param resourceId - Policy version id
 * @param dateRange - Date range filter
 * @returns List of version runs
 */
export async function fetchRunsByPolicyVersion({
    resourceId,
    dateRange,
}: {
    resourceId: string;
    dateRange: DateRange;
}): Promise<RunsResponse> {
    try {
        const data = await apiFetch<RunsResponse>("/api/runs", {
            method: "POST",
            body: JSON.stringify({ type: "policyVersion", resourceId, dateRange }),
        });

        return { runs: data.runs || null };
    } catch (error) {
        console.error("Failed to load policy version runs:", error);
        return { runs: null };
    }
}

// Components

/**
 * Creates a new workflow component
 *
 * @param componentData - Component configuration
 * @returns Created component with id
 */
export async function createComponent(componentData: ComponentBase): Promise<ComponentBase> {
    try {
        return await apiFetch<ComponentBase>("/api/proxy/components", {
            method: "POST",
            body: JSON.stringify(componentData),
        });
    } catch (error) {
        console.error("Component creation failed:", error);
        throw error;
    }
}

/**
 * Delete a component
 *
 * @param componentName - Name of component to remove
 */
export async function deleteComponent(componentName: string): Promise<void> {
    try {
        await apiFetch<void>(`/api/proxy/components/${encodeURIComponent(componentName)}`, {
            method: "DELETE",
        });
    } catch (error) {
        console.error(`Failed to delete component "${componentName}":`, error);
        throw error;
    }
}

// DataSource

/**
 * Creates a new data source connection
 *
 * @param dataSourceSpec - Data source configuration
 * @returns Created data source
 */
export async function createDataSource(dataSourceSpec: DataSourceSpec): Promise<DataSourceSpec> {
    try {
        return await apiFetch<DataSourceSpec>("/api/proxy/data-sources", {
            method: "POST",
            body: JSON.stringify(dataSourceSpec),
        });
    } catch (error) {
        console.error("Data source creation failed:", error);
        throw error;
    }
}

/**
 * Removes a data source
 *
 * @param dataSourceId - id to delete
 */
export async function deleteDataSource(dataSourceId: string): Promise<void> {
    try {
        await apiFetch<void>(`/api/proxy/data-sources/${encodeURIComponent(dataSourceId)}`, {
            method: "DELETE",
        });
    } catch (error) {
        console.error(`Failed to delete data source "${dataSourceId}":`, error);
        throw error;
    }
}

/**
 * Fetches  data source over a time
 *
 * @param dataSourceId - Data source to analyze
 * @param from - Start date
 * @param to - End date
 * @returns Usage metrics and
 */
export async function fetchDataSourceUsage(
    dataSourceId: string,
    from: string,
    to: string,
): Promise<DataSourceUsage> {
    try {
        const params = new URLSearchParams({ from, to });
        const url = `/api/proxy/data-sources/${encodeURIComponent(dataSourceId)}/usage?${params}`;

        const data = await apiFetch<DataSourceUsage>(url);
        return { usage: data.usage || [] };
    } catch (error) {
        console.error(`Failed to fetch usage for data source "${dataSourceId}":`, error);
        throw error;
    }
}

/**
 * Fetches performance metrics for a data source
 *
 * @param dataSourceId - Data source to analyze
 * @param from - Start date
 * @param to - End date
 * @returns Performance metrics data
 */
export async function fetchDataSourceMetrics(
    dataSourceId: string,
    from: string,
    to: string,
): Promise<DataSourceMetrics> {
    try {
        const params = new URLSearchParams({ from, to });
        const url = `/api/proxy/data-sources/${encodeURIComponent(dataSourceId)}/metrics?${params}`;

        const data = await apiFetch<DataSourceMetrics>(url);
        return { metrics: data.metrics || [] };
    } catch (error) {
        console.error(`Failed to fetch metrics for data source "${dataSourceId}":`, error);
        throw error;
    }
}

/**
 * Fetches cache performance
 *
 * @param dataSourceId - Data source to analyze
 * @param from - Start date
 * @param to - End date
 * @returns Cache hit rates, miss counts
 */
export async function fetchDataSourceCacheStats(
    dataSourceId: string,
    from: string,
    to: string,
): Promise<DataSourceCacheStats> {
    try {
        const params = new URLSearchParams({ from, to });
        const url = `/api/proxy/data-sources/${encodeURIComponent(dataSourceId)}/cache-stats?${params}`;
        return await apiFetch<DataSourceCacheStats>(url);
    } catch (error) {
        console.error(`Failed to fetch cache stats for data source "${dataSourceId}":`, error);
        throw error;
    }
}

// Policies

/**
 * Creates a new policy
 *
 * @param policyData - Policy configuration
 * @returns Created policy with id
 */
export async function createPolicy(policyData: PolicyCreate): Promise<Policy> {
    try {
        return await apiFetch<Policy>("/api/proxy/policies", {
            method: "POST",
            body: JSON.stringify(policyData),
        });
    } catch (error) {
        console.error("Policy creation failed:", error);
        throw error;
    }
}

/**
 * Permanently deletes a policy and all  versions
 *
 * @param policyId - Policy id to delete
 */
export async function deletePolicy(policyId: string): Promise<void> {
    try {
        await apiFetch<void>(`/api/proxy/policies/${encodeURIComponent(policyId)}`, {
            method: "DELETE",
        });
    } catch (error) {
        console.error(`Failed to delete policy "${policyId}":`, error);
        throw error;
    }
}

/**
 * Deletes a specific version of a policy
 *
 * @param policyVersionId - Policy version ID to delete
 */
export async function deletePolicyVersion(policyVersionId: string): Promise<void> {
    try {
        await apiFetch<void>(`/api/proxy/policy-versions/${encodeURIComponent(policyVersionId)}`, {
            method: "DELETE",
        });
    } catch (error) {
        console.error(`Failed to delete policy version "${policyVersionId}":`, error);
        throw error;
    }
}

//  Backtest

/**
 * Creates and launches a backtest run
 *
 * @param backtestConfig - Backtest configuration (input data and parameters)
 * @returns Created run object with  details
 */
export async function createBacktest(backtestConfig: any): Promise<any> {
    try {
        return await apiFetch<any>("/api/proxy/backtests", {
            method: "POST",
            body: JSON.stringify(backtestConfig),
        });
    } catch (error) {
        console.error("Backtest creation failed:", error);
        throw error;
    }
}

// Legacy Aliases

export const fetchMetricsDataClient = fetchPolicyMetrics;
export const fetchRunOutcomesClient = fetchRunOutcomes;
export const fetchRunsByPolicyClient = fetchRunsByPolicy;
export const fetchRunsByPolicyVersionClient = fetchRunsByPolicyVersion;
export const createComponentClient = createComponent;
export const deleteComponentClient = deleteComponent;
export const createDataSourceClient = createDataSource;
export const deleteDataSourceClient = deleteDataSource;
export const fetchDataSourceUsageClient = fetchDataSourceUsage;
export const fetchDataSourceMetricsClient = fetchDataSourceMetrics;
export const fetchDataSourceCacheStatsClient = fetchDataSourceCacheStats;
export const createPolicyClient = createPolicy;
export const deletePolicyClient = deletePolicy;
export const deletePolicyVersionClient = deletePolicyVersion;
export const createBacktestClient = createBacktest;
