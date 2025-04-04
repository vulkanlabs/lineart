"use server";

import { PolicyVersionBase } from "@vulkan-server/PolicyVersionBase";

export async function saveWorkflowSpec(policyVersionId: string, spec: any) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const request: PolicyVersionBase = {
        alias: null,
        spec: spec,
        requirements: [],
        input_schema: {
            "score": "int",
        },
    };

    return fetch(`${serverUrl}/policy-versions/${policyVersionId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
        cache: "no-store",
    })
        .then(async (response) => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}: ${response}`);
            }

            const data = await response.json();
            return { success: true, data, error: null };
        })
        .catch((error) => {
            console.error("Error saving workflow:", error);
            return { success: false, error: error.message, data: null };
        });
}
