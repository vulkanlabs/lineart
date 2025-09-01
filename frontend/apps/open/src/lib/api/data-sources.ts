"use server";

import {
    type DataSource,
    type DataSourceSpec,
    type DataSourceEnvVarBase,
} from "@vulkanlabs/client-open";
import { dataSourcesApi, withErrorHandling } from "./client";

export const fetchDataSources = async (): Promise<DataSource[]> => {
    return withErrorHandling(dataSourcesApi.listDataSources(), "fetch data sources");
};

export const fetchDataSource = async (dataSourceId: string): Promise<DataSource> => {
    return withErrorHandling(
        dataSourcesApi.getDataSource({ dataSourceId }),
        `fetch data source ${dataSourceId}`,
    );
};

export const createDataSource = async (data: DataSourceSpec) => {
    return withErrorHandling(
        dataSourcesApi.createDataSource({ dataSourceSpec: data }),
        "create data source",
    );
};

export const deleteDataSource = async (dataSourceId: string) => {
    return withErrorHandling(
        dataSourcesApi.deleteDataSource({ dataSourceId }),
        `delete data source ${dataSourceId}`,
    );
};

export const fetchDataSourceEnvVars = async (dataSourceId: string) => {
    return withErrorHandling(
        dataSourcesApi.getDataSourceEnvVariables({ dataSourceId }),
        `fetch environment variables for data source ${dataSourceId}`,
    );
};

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
