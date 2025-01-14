import { formatISO } from "date-fns";

import { CurrentUser, CurrentInternalUser } from "@stackframe/stack";
import { Component } from "@vulkan-server/Component";
import { Run } from "@vulkan-server/Run";
import { RunData } from "@vulkan-server/RunData";
import { RunLogs } from "@vulkan-server/RunLogs";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { ComponentVersion } from "@vulkan-server/ComponentVersion";

type StackUser = CurrentUser | CurrentInternalUser;

export async function getAuthHeaders(user: StackUser) {
    const { accessToken, refreshToken } = await user.getAuthJson();
    const headers = {
        "x-stack-access-token": accessToken,
        "x-stack-refresh-token": refreshToken,
    };
    return headers;
}

export async function fetchServerData({
    user,
    endpoint,
    label,
}: {
    user: StackUser;
    endpoint: string;
    label?: string;
}) {
    const headers = await getAuthHeaders(user);
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    return fetch(new URL(endpoint, serverUrl), { headers })
        .then((response) => {
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

export async function fetchPolicies(
    user: StackUser,
    includeArchived: boolean = false,
): Promise<Policy[]> {
    return fetchServerData({
        user: user,
        endpoint: `/policies?include_archived=${includeArchived}`,
        label: "list of policies",
    });
}

export async function fetchPolicy(user: StackUser, policyId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/policies/${policyId}`,
        label: `policy ${policyId}`,
    });
}

export async function fetchPolicyRuns(user: StackUser, policyId: string): Promise<Run[]> {
    return fetchServerData({
        user: user,
        endpoint: `/policies/${policyId}/runs`,
        label: `runs for policy ${policyId}`,
    });
}

export async function fetchPolicyVersionRuns(user: StackUser, policyVersionId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/policy-versions/${policyVersionId}/runs`,
        label: `runs for policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersions(
    user: StackUser,
    policyId: string,
    includeArchived: boolean = false,
) {
    return fetchServerData({
        user: user,
        endpoint: `/policies/${policyId}/versions?include_archived=${includeArchived}`,
        label: `versions for policy ${policyId}`,
    });
}

export async function fetchPolicyVersion(
    user: StackUser,
    policyVersionId: string,
): Promise<PolicyVersion> {
    return fetchServerData({
        user: user,
        endpoint: `/policy-versions/${policyVersionId}`,
        label: `policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersionVariables(user: StackUser, policyVersionId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/policy-versions/${policyVersionId}/variables`,
        label: `variables for policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersionComponents(user: StackUser, policyVersionId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/policy-versions/${policyVersionId}/components`,
        label: `component usage for policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersionDataSources(user: StackUser, policyVersionId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/policy-versions/${policyVersionId}/data-sources`,
        label: `data sources for policy version ${policyVersionId}`,
    });
}

export async function fetchComponents(
    user: StackUser,
    includeArchived: boolean = false,
): Promise<any[]> {
    return fetchServerData({
        user: user,
        endpoint: `/components?include_archived=${includeArchived}`,
        label: "list of components",
    });
}

export async function fetchComponent(user: StackUser, componentId: string): Promise<Component> {
    return fetchServerData({
        user: user,
        endpoint: `/components/${componentId}`,
        label: `component ${componentId}`,
    });
}

export async function fetchComponentVersions(
    user: StackUser,
    componentId: string,
    includeArchived: boolean = false,
) {
    return fetchServerData({
        user: user,
        endpoint: `/components/${componentId}/versions?include_archived=${includeArchived}`,
        label: `component versions for component ${componentId}`,
    });
}

export async function fetchComponentVersion(
    user: StackUser,
    componentVersionId: string,
): Promise<ComponentVersion> {
    return fetchServerData({
        user: user,
        endpoint: `/component-versions/${componentVersionId}`,
        label: `component version ${componentVersionId}`,
    });
}

export async function fetchComponentVersionUsage(user: StackUser, componentId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/components/${componentId}/usage`,
        label: `component usage for component ${componentId}`,
    });
}

export async function fetchRun(user: StackUser, runId: string): Promise<Run> {
    return fetchServerData({
        user: user,
        endpoint: `/runs/${runId}`,
        label: `run ${runId}`,
    });
}

export async function fetchRunsData(user: StackUser, runId: string): Promise<RunData> {
    return fetchServerData({
        user: user,
        endpoint: `/runs/${runId}/data`,
        label: `data for run ${runId}`,
    });
}

export async function fetchRunLogs(user: StackUser, runId: string): Promise<RunLogs> {
    return fetchServerData({
        user: user,
        endpoint: `/runs/${runId}/logs`,
        label: `logs for run ${runId}`,
    });
}

export async function fetchDataSources(user: StackUser) {
    return fetchServerData({
        user: user,
        endpoint: `/data-sources`,
        label: `data sources`,
    });
}

export async function fetchDataSource(user: StackUser, dataSourceId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/data-sources/${dataSourceId}`,
        label: `data source ${dataSourceId}`,
    });
}

export async function fetchBacktestWorkspace(user: StackUser, policyVersionId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/policy-versions/${policyVersionId}/backtest-workspace`,
        label: `policy version ${policyVersionId} backtest workspace`,
    });
}

export async function fetchPolicyVersionBacktests(user: StackUser, policyVersionId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/backtests?policy_version_id=${policyVersionId}`,
        label: `backtests for policy version ${policyVersionId}`,
    });
}

export async function fetchBacktestFiles(user: StackUser, policyVersionId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/files?policy_version_id=${policyVersionId}`,
        label: `backtests files for policy version ${policyVersionId}`,
    });
}

export async function fetchBacktest(user: StackUser, backtestId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/backtests/${backtestId}/`,
        label: `backtest ${backtestId}`,
    });
}

export async function fetchBacktestStatus(user: StackUser, backtestId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/backtests/${backtestId}/status`,
        label: `status for backtest ${backtestId}`,
    });
}

export async function fetchBacktestMetrics(
    user: StackUser,
    backtestId: string,
    target: boolean = false,
    time: boolean = false,
    column: string | null = null,
) {
    return fetchServerData({
        user: user,
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
    groupByStatus: boolean = false,
) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    return fetch(
        new URL(`/policies/${policyId}/runs/count?`, serverUrl).toString() +
            new URLSearchParams({
                start_date: formatISODate(startDate),
                end_date: formatISODate(endDate),
                group_by_status: groupByStatus.toString(),
            }),
    )
        .then((response) => response.json())
        .catch((error) => {
            throw new Error(`Error fetching runs count for policy ${policyId}`, { cause: error });
        });
}

export async function fetchRunDurationStats(policyId: string, startDate: Date, endDate: Date) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    return fetch(
        new URL(`/policies/${policyId}/runs/duration?`, serverUrl).toString() +
            new URLSearchParams({
                start_date: formatISODate(startDate),
                end_date: formatISODate(endDate),
            }),
    )
        .then((response) => response.json())
        .catch((error) => {
            throw new Error(`Error fetching run duration stats for policy ${policyId}`, {
                cause: error,
            });
        });
}

export async function fetchRunDurationByStatus(policyId: string, startDate: Date, endDate: Date) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    return fetch(
        new URL(`/policies/${policyId}/runs/duration/by_status?`, serverUrl).toString() +
            new URLSearchParams({
                start_date: formatISODate(startDate),
                end_date: formatISODate(endDate),
            }),
    )
        .then((response) => response.json())
        .catch((error) => {
            throw new Error(`Error fetching run duration stats for policy ${policyId}`, {
                cause: error,
            });
        });
}
