import { formatISO } from "date-fns";

import { CurrentUser, CurrentInternalUser } from "@stackframe/stack";

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
        .then((response) =>
            response.json().catch((error) => {
                throw new Error("Error parsing response", { cause: error });
            }),
        )
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

export async function fetchPolicyRuns(user: StackUser, policyId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/policies/${policyId}/runs`,
        label: `runs for policy ${policyId}`,
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

export async function fetchPolicyVersion(user: StackUser, policyVersionId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/policyVersions/${policyVersionId}`,
        label: `policy version ${policyVersionId}`,
    });
}

export async function fetchPolicyVersionComponents(user: StackUser, policyVersionId: string) {
    return fetchServerData({
        user: user,
        endpoint: `/policyVersions/${policyVersionId}/components`,
        label: `component usage for policy version ${policyVersionId}`,
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

export async function fetchComponent(user: StackUser, componentId: string) {
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
    componentId: string,
    componentVersionId: string,
) {
    return fetchServerData({
        user: user,
        endpoint: `/components/${componentId}/versions/${componentVersionId}`,
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
