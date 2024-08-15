import { formatISO } from "date-fns";

export async function fetchComponents(serverUrl: string) {
    return fetch(new URL("/components", serverUrl))
        .then((response) => response.json().catch((error) => {
            throw Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw Error("Error fetching components", { cause: error });
        });
};

export async function fetchPolicies(serverUrl: string) {
    return fetch(new URL("/policies", serverUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error("Error fetching policies", { cause: error });
        });
};

export async function fetchPolicy(serverUrl: string, policyId: number) {
    return fetch(new URL(`/policies/${policyId}`, serverUrl))
        .then((response) => response.json())
        .catch((error) => {
            throw new Error(`Error fetching policy ${policyId}`, { cause: error });
        });
}

export async function fetchPolicyVersions(serverUrl: string, policyId: number) {
    return fetch(new URL(`/policies/${policyId}/versions`, serverUrl))
        .then((response) => response.json())
        .catch((error) => {
            throw new Error(`Error fetching versions for policy ${policyId}`, { cause: error });
        });
}


export async function fetchComponentVersions(serverUrl: string, componentId: number) {
    return fetch(new URL(`/components/${componentId}/versions`, serverUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error(`Error fetching component versions for component ${componentId}`, { cause: error });
        });
}



export async function fetchComponentVersionUsage(
    serverUrl: string, componentId: number,
) {
    return fetch(new URL(`/components/${componentId}/usage`, serverUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error(`Error fetching component usage for component ${componentId}`, { cause: error });
        });
}

export async function fetchPolicyVersionComponents(
    serverUrl: string, policyVersionId: number,
) {
    return fetch(new URL(`/policyVersions/${policyVersionId}/components`, serverUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error(
                `Error fetching component usage for policy version ${policyVersionId}`,
                { cause: error });
        });
}

const formatISODate = (date: Date) => formatISO(date, { representation: "date" });

export async function fetchRunsCount(
    serverUrl: string, policyId: number, startDate: Date, endDate: Date,
) {
    return fetch(
        (new URL(`/policies/${policyId}/runs/count?`, serverUrl)).toString()
        + new URLSearchParams({ start_date: formatISODate(startDate), end_date: formatISODate(endDate) })
    )
        .then((response) => response.json())
        .catch((error) => {
            throw new Error(`Error fetching runs count for policy ${policyId}`, { cause: error });
        });
}