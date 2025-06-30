"use server";

import { PolicyVersionBase } from "@vulkan-server/PolicyVersionBase";
import { UIMetadata } from "@vulkan-server/UIMetadata";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { PolicyDefinitionDictInput } from "@vulkan-server/PolicyDefinitionDictInput";

export async function saveWorkflowSpec(
    policyVersion: PolicyVersion,
    spec: PolicyDefinitionDictInput,
    uiMetadata: { [key: string]: UIMetadata },
): Promise<{ success: boolean; error: string | null; data: any }> {
    if (!policyVersion || !policyVersion.policy_version_id) {
        throw new Error("Policy version ID is required");
    }
    if (!spec) {
        throw new Error("Workflow spec is required");
    }

    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

    const request: PolicyVersionBase = {
        alias: policyVersion.alias,
        spec: spec,
        requirements: [],
        input_schema: spec.input_schema,
        ui_metadata: uiMetadata,
    };

    return fetch(`${serverUrl}/policy-versions/${policyVersion.policy_version_id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
        cache: "no-store",
    })
        .then(async (response) => {
            if (!response.ok) {
                const error = await response.json();
                if (response.status !== 500) {
                    throw new Error(
                        `Server responded with status: ${response.status}: ${error.detail}`,
                    );
                } else {
                    console.error(`Server responded with status ${response.status}:`, error);
                    throw new Error(`Internal server error`);
                }
            }

            const data = await response.json();
            return { success: true, data, error: null };
        })
        .catch((error) => {
            console.error("Error saving workflow:", error);
            return { success: false, error: error.message, data: null };
        });
}

export async function fetchPolicyVersionsAction(
    policyId: string | null = null,
    includeArchived: boolean = false,
): Promise<PolicyVersion[]> {
    try {
        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) {
            throw new Error("Server URL is not defined");
        }

        const params = new URLSearchParams({
            include_archived: includeArchived.toString(),
        });

        if (policyId) {
            params.append("policy_id", policyId);
        }

        const url = `${serverUrl}/policy-versions?${params.toString()}`;

        const response = await fetch(url, {
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch policy versions: ${response.statusText}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching policy versions:", error);
        throw new Error("Failed to fetch policy versions");
    }
}
