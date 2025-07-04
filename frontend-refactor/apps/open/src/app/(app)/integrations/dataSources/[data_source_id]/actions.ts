"use server";

// Vulkan packages
import { ConfigurationVariablesBase } from "@vulkan/client-open";

// Local imports
import {
    fetchDataSourceCacheStats,
    fetchDataSourceEnvVars,
    fetchDataSourceMetrics,
    fetchDataSourceUsage,
    setDataSourceEnvVars,
} from "@/lib/api";

export async function setDataSourceVariablesAction(
    dataSourceId: string,
    variables: ConfigurationVariablesBase[],
) {
    return await setDataSourceEnvVars(dataSourceId, variables);
}

export async function fetchDataSourceEnvVarsAction(dataSourceId: string) {
    return await fetchDataSourceEnvVars(dataSourceId);
}

export async function fetchDataSourceUsageAction(
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
) {
    return await fetchDataSourceUsage(dataSourceId, startDate, endDate);
}

export async function fetchDataSourceMetricsAction(
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
) {
    return await fetchDataSourceMetrics(dataSourceId, startDate, endDate);
}

export async function fetchDataSourceCacheStatsAction(
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
) {
    return await fetchDataSourceCacheStats(dataSourceId, startDate, endDate);
}
