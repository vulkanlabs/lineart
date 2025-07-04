import { formatISO } from "date-fns";

import { Run } from "@vulkan-server/Run";
import { RunData } from "@vulkan-server/RunData";
import { RunLogs } from "@vulkan-server/RunLogs";
import { Policy } from "@vulkan-server/Policy";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { PolicyBase } from "@vulkan-server/PolicyBase";
import { PolicyVersionCreate } from "@vulkan-server/PolicyVersionCreate";
import { DataSourceSpec } from "@vulkan-server/DataSourceSpec";
import { PolicyVersionBase } from "@vulkan-server/PolicyVersionBase";
import { DataSource } from "@vulkan-server/DataSource";
import { DataSourceEnvVarBase } from "@vulkan-server/DataSourceEnvVarBase";
import { PolicyAllocationStrategy } from "@vulkan-server/PolicyAllocationStrategy";
import { ConfigurationVariablesBase } from "@vulkan-server/ConfigurationVariablesBase";

interface HTTPQueryParams {
    [key: string]: any;
}

export async function fetchServerData({
    endpoint,
    params,
    label,
}: {
    endpoint: string;
    params?: HTTPQueryParams;
    label?: string;
}): Promise<any> {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    let url = new URL(endpoint, serverUrl).toString();

    if (params) {
        const queryParams = new URLSearchParams(params);
        url += `?${queryParams.toString()}`;
    }

    return fetch(url, { cache: "no-store" })
        .then((response) => {
            if (response.status === 204) {
                return [];
            }

            if (!response.ok) {
                throw new Error(`Failed to fetch data: ${response.statusText}`, {
                    cause: response,
                });
            }
            return response.json().catch((error) => {
                throw new Error("Error parsing response", { cause: error });
            });
        })
        .catch((error) => {
            const baseMsg = "Error fetching data";
            const errorMsg = label ? `${baseMsg}: ${label}` : baseMsg;
            throw new Error(errorMsg, {
                cause: error,
            });
        });
}

export async function fetchPolicies(includeArchived: boolean = false): Promise<Policy[]> {
    return fetchServerData({
        endpoint: `/policies`,
        params: { include_archived: includeArchived },
        label: "list of policies",
    });
}

export async function fetchPolicy(policyId: string): Promise<Policy> {
    return fetchServerData({
        endpoint: `/policies/${policyId}`,
        label: `policy ${policyId}`,
    });
}

export async function createPolicy(data: PolicyBase): Promise<Policy> {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    return fetch(new URL(`/policies`, serverUrl), {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    })
        .then((response) => {
            return response.json();
        })
        .catch((error) => {
            throw new Error(`Error creating policy ${data}`, { cause: error });
        });
}

export async function deletePolicy(policyId: string) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    return fetch(new URL(`/policies/${policyId}`, serverUrl), {
        method: "DELETE",
    })
        .then((response) => {
            if (!response.ok) {
                return response.json().then((responseBody) => {
                    throw new Error(responseBody.detail, {
                        cause: response,
                    });
                });
            }
            return response.json();
        })
        .catch((error) => {
            throw new Error(`Error deleting policy: ${error}`, { cause: error });
        });
}

export async function createPolicyVersion(data: PolicyVersionCreate) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    return fetch(new URL(`/policy-versions`, serverUrl), {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    })
        .then((response) => {
            return response.json();
        })
        .catch((error) => {
            throw new Error(`create policy version: ${data}`, { cause: error });
        });
}

export async function createDataSource(data: DataSourceSpec) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    return fetch(new URL(`/data-sources`, serverUrl), {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    })
        .then((response) => {
            return response.json();
        })
        .catch((error) => {
            throw new Error(`Error creating data source ${data}`, { cause: error });
        });
}

export async function updatePolicyAllocationStrategy(
    policyId: string,
    data: PolicyAllocationStrategy,
) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    if (!serverUrl) {
        throw new Error("Server URL is not defined");
    }
    const body: PolicyBase = {
        allocation_strategy: data,
    };

    return fetch(new URL(`/policies/${policyId}`, serverUrl), {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    })
        .then(async (response) => {
            if (!response.ok) {
                const errorData = await response
                    .json()
                    .catch(() => ({ detail: "Unknown error updating allocation strategy." }));
                console.error("Failed to update policy allocation strategy", {
                    status: response.status,
                    errorData,
                });
                throw new Error(
                    errorData.detail ||
                        `Failed to update allocation strategy for policy ${policyId}`,
                );
            }
            return response.json();
        })
        .catch((error) => {
            console.error(
                `Error updating policy allocation strategy for policy ${policyId}:`,
                error,
            );
            throw error;
        });
}

export async function deleteDataSource(dataSourceId: string) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    return fetch(new URL(`/data-sources/${dataSourceId}`, serverUrl), {
        method: "DELETE",
    })
        .then((response) => {
            if (!response.ok) {
                return response.json().then((responseBody) => {
                    throw new Error(responseBody.detail, {
                        cause: response,
                    });
                });
            }
            return response.json();
        })
        .catch((error) => {
            throw new Error(`Error deleting data source: ${error}`, { cause: error });
        });
}

export async function updatePolicyVersion(policyVersionId: string, data: PolicyVersionBase) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    if (!serverUrl) {
        throw new Error("Server URL is not defined");
    }
    if (!policyVersionId) {
        throw new Error("Policy version ID is not defined");
    }

    return fetch(new URL(`/policy-versions/${policyVersionId}`, serverUrl), {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    }).then(async (response) => {
        const responseData = await response.json();
        if (!response.ok) {
            console.error(`Failed to update policy version ${policyVersionId}`, {
                status: response.status,
                response: responseData,
            });

            throw new Error(`Failed to update policy version ${policyVersionId}`, {
                cause: responseData,
            });
        }
        return responseData;
    });
}

export async function deletePolicyVersion(policyVersionId: string) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    return fetch(new URL(`/policy-versions/${policyVersionId}`, serverUrl), {
        method: "DELETE",
    })
        .then((response) => {
            if (!response.ok) {
                return response.json().then((responseBody) => {
                    throw new Error(responseBody.detail, {
                        cause: response,
                    });
                });
            }
            return response.json();
        })
        .catch((error) => {
            throw new Error(`Error deleting policy version: ${error}`, { cause: error });
        });
}

export async function fetchPolicyRuns(
    policyId: string,
    startDate: Date,
    endDate: Date,
): Promise<Run[]> {
    return fetchServerData({
        endpoint: `/policies/${policyId}/runs`,
        params: {
            start_date: formatISODate(startDate),
            end_date: formatISODate(endDate),
        },
        label: `runs for policy ${policyId}`,
    });
}

export async function fetchPolicyVersionRuns(
    policyVersionId: string,
    startDate: Date,
    endDate: Date,
): Promise<Run[]> {
    return fetchServerData({
        endpoint: `/policy-versions/${policyVersionId}/runs`,
        params: {
            start_date: formatISODate(startDate),
            end_date: formatISODate(endDate),
        },
        label: `runs for policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersions(
    policyId: string | null = null,
    includeArchived: boolean = false,
): Promise<PolicyVersion[]> {
    const params: HTTPQueryParams = {
        include_archived: includeArchived,
    };
    if (policyId) {
        params.policy_id = policyId;
    }
    return fetchServerData({
        endpoint: `/policy-versions`,
        params: params,
        label: `versions for policy ${policyId}`,
    });
}

export async function fetchPolicyVersion(policyVersionId: string): Promise<PolicyVersion> {
    return fetchServerData({
        endpoint: `/policy-versions/${policyVersionId}`,
        label: `policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersionVariables(policyVersionId: string) {
    return fetchServerData({
        endpoint: `/policy-versions/${policyVersionId}/variables`,
        label: `variables for policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersionComponents(policyVersionId: string) {
    return fetchServerData({
        endpoint: `/policy-versions/${policyVersionId}/components`,
        label: `component usage for policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersionDataSources(policyVersionId: string) {
    return fetchServerData({
        endpoint: `/policy-versions/${policyVersionId}/data-sources`,
        label: `data sources for policy version ${policyVersionId}`,
    });
}

export async function setPolicyVersionVariables(
    policyVersionId: string,
    variables: ConfigurationVariablesBase[],
) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    if (!serverUrl) {
        throw new Error("Server URL is not defined");
    }
    if (!policyVersionId) {
        throw new Error("Policy version ID is not defined");
    }

    return fetch(new URL(`/policy-versions/${policyVersionId}/variables`, serverUrl), {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(variables),
    }).then(async (response) => {
        const responseData = await response.json().catch(() => ({})); // Catch if body is empty or not json
        if (!response.ok) {
            console.error(`Failed to set variables for policy version ${policyVersionId}`, {
                status: response.status,
                response: responseData,
            });
            const detail =
                responseData.detail ||
                `Failed to set variables for policy version ${policyVersionId}`;
            throw new Error(detail, {
                cause: responseData,
            });
        }
        return responseData;
    });
}

export async function fetchComponents(includeArchived: boolean = false): Promise<any[]> {
    return fetchServerData({
        endpoint: `/components?include_archived=${includeArchived}`,
        label: "list of components",
    });
}

export async function fetchComponent(componentId: string) {
    return fetchServerData({
        endpoint: `/components/${componentId}`,
        label: `component ${componentId}`,
    });
}

export async function fetchComponentVersions(
    componentId: string,
    includeArchived: boolean = false,
) {
    return fetchServerData({
        endpoint: `/components/${componentId}/versions?include_archived=${includeArchived}`,
        label: `component versions for component ${componentId}`,
    });
}

export async function fetchComponentVersion(componentVersionId: string) {
    return fetchServerData({
        endpoint: `/component-versions/${componentVersionId}`,
        label: `component version ${componentVersionId}`,
    });
}

export async function fetchComponentVersionUsage(componentId: string) {
    return fetchServerData({
        endpoint: `/components/${componentId}/usage`,
        label: `component usage for component ${componentId}`,
    });
}

export async function fetchRun(runId: string): Promise<Run> {
    return fetchServerData({
        endpoint: `/runs/${runId}`,
        label: `run ${runId}`,
    });
}

export async function fetchRunData(runId: string): Promise<RunData> {
    return fetchServerData({
        endpoint: `/runs/${runId}/data`,
        label: `data for run ${runId}`,
    });
}

export async function fetchRunLogs(runId: string): Promise<RunLogs> {
    return fetchServerData({
        endpoint: `/runs/${runId}/logs`,
        label: `logs for run ${runId}`,
    });
}

export async function fetchDataSources(): Promise<DataSource[]> {
    return fetchServerData({
        endpoint: `/data-sources`,
        label: `data sources`,
    });
}

export async function fetchDataSource(dataSourceId: string): Promise<DataSource> {
    return fetchServerData({
        endpoint: `/data-sources/${dataSourceId}`,
        label: `data source ${dataSourceId}`,
    });
}

export async function fetchDataSourceUsage(
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
): Promise<any> {
    return fetchServerData({
        endpoint: `/data-sources/${dataSourceId}/usage`,
        params: {
            start_date: formatISODate(startDate),
            end_date: formatISODate(endDate),
        },
        label: `usage for data source ${dataSourceId}`,
    });
}

export async function fetchDataSourceMetrics(
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
): Promise<any> {
    return fetchServerData({
        endpoint: `/data-sources/${dataSourceId}/metrics`,
        params: {
            start_date: formatISODate(startDate),
            end_date: formatISODate(endDate),
        },
        label: `metrics for data source ${dataSourceId}`,
    });
}

export async function fetchDataSourceCacheStats(
    dataSourceId: string,
    startDate: Date,
    endDate: Date,
): Promise<any> {
    return fetchServerData({
        endpoint: `/data-sources/${dataSourceId}/cache-stats`,
        params: {
            start_date: formatISODate(startDate),
            end_date: formatISODate(endDate),
        },
        label: `cache statistics for data source ${dataSourceId}`,
    });
}

export async function fetchBacktestWorkspace(policyVersionId: string) {
    return fetchServerData({
        endpoint: `/policy-versions/${policyVersionId}/backtest-workspace`,
        label: `policy version ${policyVersionId} backtest workspace`,
    });
}

export async function fetchPolicyVersionBacktests(policyVersionId: string) {
    return fetchServerData({
        endpoint: `/backtests?policy_version_id=${policyVersionId}`,
        label: `backtests for policy version ${policyVersionId}`,
    });
}

export async function listUploadedFiles() {
    return fetchServerData({
        endpoint: `/files`,
        label: `backtests files`,
    });
}

export async function fetchBacktest(backtestId: string) {
    return fetchServerData({
        endpoint: `/backtests/${backtestId}/`,
        label: `backtest ${backtestId}`,
    });
}

export async function fetchBacktestStatus(backtestId: string) {
    return fetchServerData({
        endpoint: `/backtests/${backtestId}/status`,
        label: `status for backtest ${backtestId}`,
    });
}

export async function fetchBacktestMetrics(
    backtestId: string,
    target: boolean = false,
    time: boolean = false,
    column: string | null = null,
) {
    return fetchServerData({
        endpoint: `/backtests/${backtestId}/metrics/data`,
        params: {
            target,
            time,
            column: column ? column : "",
        },
        label: `example metric for backtest ${backtestId}`,
    });
}

export async function fetchDataSourceEnvVars(dataSourceId: string) {
    return fetchServerData({
        endpoint: `/data-sources/${dataSourceId}/variables`,
        label: `environment variables for data source ${dataSourceId}`,
    });
}

export async function setDataSourceEnvVars(
    dataSourceId: string,
    variables: DataSourceEnvVarBase[],
): Promise<{ data_source_id: string; variables: DataSourceEnvVarBase[] }> {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    return fetch(new URL(`/data-sources/${dataSourceId}/variables`, serverUrl), {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(variables),
    })
        .then(async (response) => {
            if (!response.ok) {
                const errorData = await response
                    .json()
                    .catch(() => ({ detail: "Unknown error setting environment variables." }));
                console.error("Failed to set data source environment variables", {
                    status: response.status,
                    errorData,
                });
                throw new Error(
                    errorData.detail ||
                        `Failed to set environment variables for data source ${dataSourceId}`,
                );
            }
            return response.json();
        })
        .catch((error) => {
            console.error(
                `Error setting environment variables for data source ${dataSourceId}:`,
                error,
            );
            throw error;
        });
}

const formatISODate = (date: Date) => formatISO(date, { representation: "date" });

export async function fetchRunsCount(
    policyId: string,
    startDate: Date,
    endDate: Date,
    versions: string[] = null,
) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const url =
        new URL(`/policies/${policyId}/runs/count?`, serverUrl).toString() +
        new URLSearchParams({
            start_date: formatISODate(startDate),
            end_date: formatISODate(endDate),
        });
    return fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ versions }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Failed to fetch runs count for policy ${policyId}`, {
                    cause: response,
                });
            }
            return response.json();
        })
        .catch((error) => {
            throw new Error(`Error fetching runs count for policy ${policyId}`, { cause: error });
        });
}

export async function fetchRunOutcomes(
    policyId: string,
    startDate: Date,
    endDate: Date,
    versions: string[] = null,
) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const url =
        new URL(`/policies/${policyId}/runs/outcomes?`, serverUrl).toString() +
        new URLSearchParams({
            start_date: formatISODate(startDate),
            end_date: formatISODate(endDate),
        });
    return fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ versions }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Failed to fetch run outcomes for policy ${policyId}`, {
                    cause: response,
                });
            }
            return response.json();
        })
        .catch((error) => {
            throw new Error(`Error fetching run outcomes for policy ${policyId}`, { cause: error });
        });
}

export async function fetchRunDurationStats(
    policyId: string,
    startDate: Date,
    endDate: Date,
    versions: string[] = null,
) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const url =
        new URL(`/policies/${policyId}/runs/duration?`, serverUrl).toString() +
        new URLSearchParams({
            start_date: formatISODate(startDate),
            end_date: formatISODate(endDate),
        });
    return fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ versions }),
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Failed to fetch run duration stats for policy ${policyId}`, {
                    cause: response,
                });
            }
            return response.json();
        })
        .catch((error) => {
            throw new Error(`Error fetching run duration stats for policy ${policyId}`, {
                cause: error,
            });
        });
}

export async function fetchRunDurationByStatus(
    policyId: string,
    startDate: Date,
    endDate: Date,
    versions: string[] = null,
) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const url =
        new URL(`/policies/${policyId}/runs/duration/by_status?`, serverUrl).toString() +
        new URLSearchParams({
            start_date: formatISODate(startDate),
            end_date: formatISODate(endDate),
        });
    return fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ versions }),
    })
        .then((response) => response.json())
        .catch((error) => {
            throw new Error(`Error fetching run duration stats for policy ${policyId}`, {
                cause: error,
            });
        });
}
