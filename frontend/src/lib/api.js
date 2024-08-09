

export async function fetchComponents(baseUrl) {
    return fetch(new URL("/components", baseUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error("Error fetching components", { cause: error });
        });
};

export async function fetchPolicies(baseUrl) {
    return fetch(new URL("/policies", baseUrl))
        .then((response) => response.json().catch((error) => {
            throw new Error("Error parsing response", { cause: error });
        }))
        .catch((error) => {
            throw new Error("Error fetching policies", { cause: error });
        });
};

export async function fetchPolicy(baseUrl, policyId) {
    return fetch(new URL(`/policies/${policyId}`, baseUrl))
        .then((response) => response.json())
        .catch((error) => {
            throw new Error(`Error fetching policy ${policyId}`, { cause: error });
        });
}