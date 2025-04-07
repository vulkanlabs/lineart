"use server";

import { PolicyVersionBase } from "@vulkan-server/PolicyVersionBase";
import { NodeDefinition } from "./types";

export async function saveWorkflowSpec(policyVersionId: string, nodes: NodeDefinition[]) {
    if (!policyVersionId) {
        throw new Error("Policy version ID is required");
    }
    if (!nodes) {
        throw new Error("Workflow spec is required");
    }
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const spec = {
        nodes: nodes,
        input_schema: {
            score: "int",
        },
    };

    const request: PolicyVersionBase = {
        alias: null,
        spec: spec,
        requirements: [],
        input_schema: {},
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
