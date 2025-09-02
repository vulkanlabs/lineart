"use server";

import {
    type DataSource,
    type DataSourceSpec,
    type DataSourceEnvVarBase,
} from "@vulkanlabs/client-open";
import { dataSourcesApi, withErrorHandling } from "./client";

/**
 * Get all available data sources
 * @returns {Promise<DataSource[]>} List of configured data sources (databases, APIs, etc.)
 */
export const fetchDataSources = async (): Promise<DataSource[]> => {
    return withErrorHandling(dataSourcesApi.listDataSources(), "fetch data sources");
};

/**
 * Get detailed info for a specific data source
 * @param {string} dataSourceId - Unique identifier of the data source
 * @returns {Promise<DataSource>} Complete data source configuration and status
 *
 * Connection details, credentials, usage stats, health status
 */
export const fetchDataSource = async (dataSourceId: string): Promise<DataSource> => {
    return withErrorHandling(
        dataSourcesApi.getDataSource({ dataSourceId }),
        `fetch data source ${dataSourceId}`,
    );
};

/**
 * Create a new data source connection
 * @param {DataSourceSpec} data - Data source configuration (type, connection details, credentials)
 * @returns {Promise<DataSource>} Created data source with generated ID
 */
export const createDataSource = async (data: DataSourceSpec) => {
    return withErrorHandling(
        dataSourcesApi.createDataSource({ dataSourceSpec: data }),
        "create data source",
    );
};

/**
 * Delete/remove a data source
 * @param {string} dataSourceId - ID of data source to remove
 * @returns {Promise<void>} Success or throws error
 *
 * This will break any workflows/policies using this data source
 */
export const deleteDataSource = async (dataSourceId: string) => {
    return withErrorHandling(
        dataSourcesApi.deleteDataSource({ dataSourceId }),
        `delete data source ${dataSourceId}`,
    );
};

/**
 * Get environment variables for a data source
 * @param {string} dataSourceId - Target data source ID
 * @returns {Promise<DataSourceEnvVar[]>} Array of environment variable configs
 *
 * Variable names, values (masked for security), types
 */
export const fetchDataSourceEnvVars = async (dataSourceId: string) => {
    return withErrorHandling(
        dataSourcesApi.getDataSourceEnvVariables({ dataSourceId }),
        `fetch environment variables for data source ${dataSourceId}`,
    );
};

/**
 * Update environment variables for a data source
 * @param {string} dataSourceId - Target data source ID
 * @param {DataSourceEnvVarBase[]} variables - Array of env var objects to set
 * @returns {Promise<void>} Success or throws error
 */
export const setDataSourceEnvVars = async (
    dataSourceId: string,
    variables: DataSourceEnvVarBase[],
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
 * @returns {Promise<any>} Usage metrics including query counts, data transferred, connection stats
 *
 * Total queries, avg response time, data volume, error rates
 */
export const fetchDataSourceUsage = async (
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
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
 * @returns {Promise<any>} Performance metrics and health data
 *
 * Response times, error rates, connection counts, throughput
 */
export const fetchDataSourceMetrics = async (
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
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
 * @returns {Promise<any>} Cache metrics including hit/miss rates, cache size, evictions
 */
export const fetchDataSourceCacheStats = async (
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
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
