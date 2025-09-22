// Workflow save API - Uses direct server communication
import {
    PolicyDefinitionDict,
    UIMetadata,
    PolicyVersion,
    Component,
    ComponentUpdate,
} from "@vulkanlabs/client-open";
import { updateComponent } from "@/lib/api";
import { apiResult } from "@/lib/api-response";


export async function PUT(request: Request) {
    try {
        const { workflow, spec, uiMetadata = {} } = await request.json();

        if (workflow?.policy_version_id) return savePolicyVersion(workflow, spec, uiMetadata);
        else if (workflow?.component_id) return saveComponent(workflow, spec, uiMetadata);
        else return apiResult.error("Invalid workflow type", 400);
    } catch (error) {
        return apiResult.error(error instanceof Error ? error.message : "Save failed", 500);
    }
}

async function saveComponent(
    component: Component,
    spec: PolicyDefinitionDict,
    uiMetadata: { [key: string]: UIMetadata },
) {
    try {
        const requestBody: ComponentUpdate = {
            name: component.name,
            description: component.description || null,
            icon: component.icon || null,
            workflow: {
                spec,
                requirements: component.workflow?.requirements || [],
                variables: component.workflow?.variables || [],
                ui_metadata: uiMetadata,
            },
        };

        const response = await updateComponent(component.component_id, requestBody);
        return apiResult.success(response);
    } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        return apiResult.error(`Save failed: ${message}`);
    }
}

async function savePolicyVersion(
    policyVersion: PolicyVersion,
    spec: PolicyDefinitionDict,
    uiMetadata: { [key: string]: UIMetadata },
) {
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    if (!serverUrl) return apiResult.error("Server URL is not configured");

    try {
        const requestBody = {
            alias: policyVersion.alias || null,
            workflow: {
                spec,
                requirements: policyVersion.workflow?.requirements || [],
                ui_metadata: uiMetadata,
                variables: policyVersion.workflow?.variables || [],
            },
        };

        const response = await fetch(
            `${serverUrl}/policy-versions/${policyVersion.policy_version_id}`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(requestBody),
                cache: "no-store",
            },
        );

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            const message = error.detail || error.message || response.statusText;
            return apiResult.error(`Save failed: ${message}`, response.status);
        }

        const data = await response.json();
        return apiResult.success(data);
    } catch (error) {
        const message = error instanceof Error ? error.message : "Network error";
        return apiResult.error(`Save failed: ${message}`);
    }
}
