

export async function fetchComponents(serverUrl) {
    return fetch(new URL("/components", serverUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error("Error fetching components", { cause: error });
        });
};

export async function fetchPolicies(serverUrl) {
    return fetch(new URL("/policies", serverUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error("Error fetching policies", { cause: error });
        });
};

export async function fetchPolicy(serverUrl, policyId) {
    return fetch(new URL(`/policies/${policyId}`, serverUrl))
        .then((response) => response.json())
        .catch((error) => {
            throw new Error(`Error fetching policy ${policyId}`, { cause: error });
        });
}



export async function fetchComponentVersions(serverUrl, componentId) {
    return fetch(new URL(`/components/${componentId}/versions`, serverUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error(`Error fetching component versions for component ${componentId}`, { cause: error });
        });
}



export async function fetchComponentVersionUsage(serverUrl, componentId = null, policyVersionId = null) {
    return fetch(new URL(`/components/${componentId}/usage`, serverUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error(`Error fetching component usage for component ${componentId}`, { cause: error });
        });
}