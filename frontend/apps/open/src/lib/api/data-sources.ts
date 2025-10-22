"use server";

import {
    type DataSource,
    type DataSourceSpec,
    type DataSourceEnvVarBase,
} from "@vulkanlabs/client-open";
import { dataSourcesApi, withErrorHandling } from "./client";

/**
 * Get all available data sources
 * @param {boolean} [includeArchived=false] - Include archived data sources
 * @param {string} [status] - Filter by status (e.g., 'PUBLISHED', 'DRAFT', 'ARCHIVED')
 * @returns {Promise<DataSource[]>} List of configured data sources (databases, APIs, etc.)
 */
export const fetchDataSources = async (
    includeArchived: boolean = false,
    status?: string,
): Promise<DataSource[]> => {
    return withErrorHandling(
        dataSourcesApi.listDataSources({ includeArchived, status }),
        "fetch data sources",
    );
};

/**
 * Get detailed info for a specific data source
 * @param {string} dataSourceId - Unique identifier of the data source
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<DataSource>} Complete data source configuration and status
 *
 * Connection details, credentials, usage stats, health status
 */
export const fetchDataSource = async (
    dataSourceId: string,
    projectId?: string,
): Promise<DataSource> => {
    return withErrorHandling(
        dataSourcesApi.getDataSource({ dataSourceId }),
        `fetch data source ${dataSourceId}`,
    );
};

/**
 * Create a new data source connection
 * @param {DataSourceSpec} data - Data source configuration (type, connection details, credentials)
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<DataSource>} Created data source with generated ID
 */
export const createDataSource = async (
    data: DataSourceSpec,
    projectId?: string,
): Promise<DataSource> => {
    return withErrorHandling(
        dataSourcesApi.createDataSource({ dataSourceSpec: data }),
        "create data source",
    );
};

/**
 * Delete/remove a data source
 * @param {string} dataSourceId - ID of data source to remove
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<void>} Success or throws error
 *
 * This will break any workflows/policies using this data source
 */
export const deleteDataSource = async (dataSourceId: string, projectId?: string) => {
    return withErrorHandling(
        dataSourcesApi.deleteDataSource({ dataSourceId }),
        `delete data source ${dataSourceId}`,
    );
};

/**
 * Get environment variables for a data source
 * @param {string} dataSourceId - Target data source ID
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<DataSourceEnvVar[]>} Array of environment variable configs
 *
 * Variable names, values (masked for security), types
 */
export const fetchDataSourceEnvVars = async (dataSourceId: string, projectId?: string) => {
    return withErrorHandling(
        dataSourcesApi.getDataSourceEnvVariables({ dataSourceId }),
        `fetch environment variables for data source ${dataSourceId}`,
    );
};

/**
 * Update environment variables for a data source
 * @param {string} dataSourceId - Target data source ID
 * @param {DataSourceEnvVarBase[]} variables - Array of env var objects to set
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<void>} Success or throws error
 */
export const setDataSourceEnvVars = async (
    dataSourceId: string,
    variables: DataSourceEnvVarBase[],
    projectId?: string,
) => {
    return withErrorHandling(
        dataSourcesApi.setDataSourceEnvVariables({
            dataSourceId,
            dataSourceEnvVarBase: variables,
        }),
        `set environment variables for data source ${dataSourceId}`,
    );
};

// Usage and metrics
/**
 * Get data source usage analytics over time period
 * @param {string} dataSourceId - Target data source identifier
 * @param {Date} startDate - Analytics period start
 * @param {Date} endDate - Analytics period end
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<any>} Usage metrics including query counts, data transferred, connection stats
 *
 * Total queries, avg response time, data volume, error rates
 */
export const fetchDataSourceUsage = async (
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
    projectId?: string,
): Promise<any> => {
    return withErrorHandling(
        dataSourcesApi.getDataSourceUsage({
            dataSourceId,
            startDate,
            endDate,
        }),
        `fetch usage for data source ${dataSourceId}`,
    );
};

/**
 * Get performance and health metrics for a data source
 * @param {string} dataSourceId - Data source to analyze
 * @param {Date} startDate - Metrics period start
 * @param {Date} endDate - Metrics period end
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<any>} Performance metrics and health data
 *
 * Response times, error rates, connection counts, throughput
 */
export const fetchDataSourceMetrics = async (
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
    projectId?: string,
): Promise<any> => {
    return withErrorHandling(
        dataSourcesApi.getDataSourceMetrics({
            dataSourceId,
            startDate,
            endDate,
        }),
        `fetch metrics for data source ${dataSourceId}`,
    );
};

/**
 * Get cache performance statistics for a data source
 * @param {string} dataSourceId - Data source to analyze
 * @param {Date} startDate - Stats period start
 * @param {Date} endDate - Stats period end
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<any>} Cache metrics including hit/miss rates, cache size, evictions
 */
export const fetchDataSourceCacheStats = async (
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
    projectId?: string,
): Promise<any> => {
    return withErrorHandling(
        dataSourcesApi.getCacheStatistics({
            dataSourceId,
            startDate,
            endDate,
        }),
        `fetch cache statistics for data source ${dataSourceId}`,
    );
};

/**
 * Update an existing data source configuration
 *
 * The backend enforces update restrictions for published data sources.
 * This function simply sends the requested updates and lets the backend
 * decide what changes are allowed based on the data source status.
 *
 * @param {string} dataSourceId - ID of data source to update
 * @param {Partial<DataSourceSpec>} updates - Partial updates to apply
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<DataSource>} Updated data source
 */
export async function updateDataSource(
    dataSourceId: string,
    updates: Partial<DataSourceSpec>,
    projectId?: string,
): Promise<DataSource> {
    "use server";
    return withErrorHandling(
        dataSourcesApi.updateDataSource({
            dataSourceId,
            dataSourceSpec: updates as DataSourceSpec,
        }),
        `update data source ${dataSourceId}`,
    );
}

/**
 * Test a data source without persisting to database
 *
 * The backend handles fetching the data source configuration and merging
 * with runtime parameters and environment variables.
 *
 * @param {string} dataSourceId - ID of data source to test
 * @param {object} testRequest - Test configuration
 * @param {any} testRequest.configured_params - Runtime parameters for the test
 * @param {any} [testRequest.override_env_vars] - Optional environment variables to override
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<any>} Test response with status, body, timing
 */
export const testDataSource = async (
    dataSourceId: string,
    testRequest: {
        configured_params: any;
        override_env_vars?: any;
    },
    projectId?: string,
): Promise<{
    test_id: string;
    status_code: number;
    response_body: any;
    response_time_ms: number;
    response_headers: Record<string, string>;
    error?: string;
}> => {
    const response = await fetch(
        `${process.env.VULKAN_SERVER_URL}/data-sources/${dataSourceId}/test`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                params: testRequest.configured_params || {},
                env_vars: testRequest.override_env_vars || {},
            }),
        },
    );

    if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to test data source ${dataSourceId}: ${error}`);
    }

    return response.json();
};

/**
 * Publish a data source (change status from draft to published)
 * Once published, a data source becomes read-only and available in workflows
 * @param {string} dataSourceId - ID of data source to publish
 * @param {string} [projectId] - Optional project context
 * @returns {Promise<DataSource>}
 */
export const publishDataSource = async (
    dataSourceId: string,
    projectId?: string,
): Promise<DataSource> => {
    return withErrorHandling(
        dataSourcesApi.publishDataSource({ dataSourceId }),
        `publish data source ${dataSourceId}`,
    );
};
