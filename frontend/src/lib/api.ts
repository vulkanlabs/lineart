import { formatISO } from "date-fns";

import { Run } from "@vulkan-server/Run";
import { RunData } from "@vulkan-server/RunData";
import { RunLogs } from "@vulkan-server/RunLogs";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { PolicyBase } from "@vulkan-server/PolicyBase";
import { PolicyVersionCreate } from "@vulkan-server/PolicyVersionCreate";

export async function fetchServerData({ endpoint, label }: { endpoint: string; label?: string }) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    return fetch(new URL(endpoint, serverUrl))
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

type Policy = {
    policy_id: string;
    name: string;
    description: string;
    input_schema: string;
    output_schema: string;
    active_policy_version_id?: string;
    created_at: string;
    last_updated_at: string;
};

export async function fetchPolicies(includeArchived: boolean = false): Promise<Policy[]> {
    return fetchServerData({
        endpoint: `/policies?include_archived=${includeArchived}`,
        label: "list of policies",
    });
}

export async function fetchPolicy(policyId: string) {
    return fetchServerData({
        endpoint: `/policies/${policyId}`,
        label: `policy ${policyId}`,
    });
}

export async function createPolicy(data: PolicyBase) {
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
            throw new Error(`Error policy version ${data}`, { cause: error });
        });
}

export async function fetchPolicyRuns(policyId: string): Promise<Run[]> {
    return fetchServerData({
        endpoint: `/policies/${policyId}/runs`,
        label: `runs for policy ${policyId}`,
    });
}

export async function fetchPolicyVersionRuns(policyVersionId: string) {
    return fetchServerData({
        endpoint: `/policy-versions/${policyVersionId}/runs`,
        label: `runs for policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersions(
    policyId: string,
    includeArchived: boolean = false,
): Promise<PolicyVersion[]> {
    return fetchServerData({
        endpoint: `/policies/${policyId}/versions?include_archived=${includeArchived}`,
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

export async function fetchRunsData(runId: string): Promise<RunData> {
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

export async function fetchDataSources() {
    return fetchServerData({
        endpoint: `/data-sources`,
        label: `data sources`,
    });
}

export async function fetchDataSource(dataSourceId: string) {
    return fetchServerData({
        endpoint: `/data-sources/${dataSourceId}`,
        label: `data source ${dataSourceId}`,
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
        endpoint: `/backtests/${backtestId}/metrics/data?target=${target}&time=${time}${column ? `&column=${column}` : ""}`,
        label: `example metric for backtest ${backtestId}`,
    });
}

// UNAUTHENTICATED CALLS:
// ----------------------

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
