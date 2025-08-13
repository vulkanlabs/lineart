// OSS App - Shared API patterns (inline approach)
import {
    PolicyVersionBase,
    PolicyDefinitionDictInput,
    UIMetadata,
    PolicyVersion,
    Component,
    ComponentBase,
} from "@vulkanlabs/client-open";
import { updateComponent } from "@/lib/api";

// Shared response pattern
const apiResponse = {
    success: (data: any) => Response.json({ success: true, data, error: null }),
    error: (message: string, status: number = 500) => {
        console.error(`API Error: ${message}`);
        return Response.json({ success: false, error: message, data: null }, { status });
    }
};

// Shared validation pattern
function validateWorkflow(workflow: any, spec: any): string | null {
    if (!workflow) return "Workflow is required";
    if (!spec) return "Workflow spec is required";
    return null;
}

export async function PUT(request: Request) {
    try {
        const { workflow, spec, uiMetadata }: {
            workflow: any;
            spec: PolicyDefinitionDictInput;
            uiMetadata: { [key: string]: UIMetadata };
        } = await request.json();

        const validationError = validateWorkflow(workflow, spec);
        if (validationError) return apiResponse.error(validationError, 400);

        // Handle workflow types
        if (typeof workflow === "object" && "policy_version_id" in workflow) {
            return savePolicyVersion(workflow as PolicyVersion, spec, uiMetadata);
        } else if (typeof workflow === "object" && "component_id" in workflow) {
            return saveComponent(workflow as Component, spec, uiMetadata);
        } else {
            return apiResponse.error("Invalid workflow type", 400);
        }
    } catch (error) {
        return apiResponse.error(error instanceof Error ? error.message : "Unknown error");
    }
}

async function saveComponent(component: Component, spec: PolicyDefinitionDictInput, uiMetadata: { [key: string]: UIMetadata }) {
    try {
        const requestBody: ComponentBase = {
            requirements: component.workflow?.requirements || [],
            name: component.name,
            description: component.description || null,
            icon: component.icon || null,
            spec,
            variables: component.workflow?.variables || [],
            ui_metadata: uiMetadata,
        };
        const response = await updateComponent(component.component_id, requestBody);
        return apiResponse.success(response);
    } catch (error) {
        return apiResponse.error(error instanceof Error ? error.message : "Failed to save component");
    }
}

async function savePolicyVersion(policyVersion: PolicyVersion, spec: PolicyDefinitionDictInput, uiMetadata: { [key: string]: UIMetadata }) {
    try {
        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) return apiResponse.error("Server URL is not configured");

        const requestBody: PolicyVersionBase = {
            alias: policyVersion.alias || null,
            spec,
            requirements: [],
            ui_metadata: uiMetadata,
        };

        const response = await fetch(`${serverUrl}/policy-versions/${policyVersion.policy_version_id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody),
            cache: "no-store",
        });

        if (!response.ok) {
            const error = await response.json();
            return apiResponse.error(
                response.status !== 500 ? `Server error ${response.status}: ${error.detail}` : "Internal server error",
                response.status
            );
        }

        const data = await response.json();
        return apiResponse.success(data);
    } catch (error) {
        return apiResponse.error(error instanceof Error ? error.message : "Failed to save policy version");
    }
}