// Workflow save API - Uses direct server communication
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
    },
};

// Shared validation pattern
function validateWorkflow(workflow: any, spec: any): string | null {
    if (!workflow) return "Workflow is required";
    if (!spec) return "Workflow spec is required";
    return null;
}

export async function PUT(request: Request) {
    try {
        const {
            workflow,
            spec,
            uiMetadata,
            isAutoSave = false,
        }: {
            workflow: any;
            spec: PolicyDefinitionDictInput;
            uiMetadata: { [key: string]: UIMetadata };
            isAutoSave?: boolean;
        } = await request.json();

        const validationError = validateWorkflow(workflow, spec);
        if (validationError) return apiResponse.error(validationError, 400);

        // Handle workflow types
        if (typeof workflow === "object" && "policy_version_id" in workflow) {
            return savePolicyVersion(workflow as PolicyVersion, spec, uiMetadata, isAutoSave);
        } else if (typeof workflow === "object" && "component_id" in workflow) {
            return saveComponent(workflow as Component, spec, uiMetadata, isAutoSave);
        } else {
            return apiResponse.error("Invalid workflow type", 400);
        }
    } catch (error) {
        return apiResponse.error(error instanceof Error ? error.message : "Unknown error");
    }
}

async function saveComponent(
    component: Component,
    spec: PolicyDefinitionDictInput,
    uiMetadata: { [key: string]: UIMetadata },
    isAutoSave: boolean = false,
) {
    try {
        // For auto-save, we can skip heavy validation or processing
        if (isAutoSave) console.log("Auto-saving component:", component.name);

        const requestBody: ComponentBase = {
            name: component.name,
            description: component.description || null,
            icon: component.icon || null,
            spec: spec ?? component.workflow?.spec,
            requirements: component.workflow?.requirements || [],
            variables: component.workflow?.variables || [],
            ui_metadata: uiMetadata ?? component.workflow?.ui_metadata,
        };
        const response = await updateComponent(component.name, requestBody);
        return apiResponse.success(response);
    } catch (error) {
        const errorMessage = isAutoSave ? "Auto-save failed" : "Failed to save component";
        return apiResponse.error(
            error instanceof Error ? error.message : errorMessage,
        );
    }
}

async function savePolicyVersion(
    policyVersion: PolicyVersion,
    spec: PolicyDefinitionDictInput,
    uiMetadata: { [key: string]: UIMetadata },
    isAutoSave: boolean = false,
) {
    try {
        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) return apiResponse.error("Server URL is not configured");

        // For auto-save, we can optimize the request
        if (isAutoSave) console.log("Auto-saving policy version:", policyVersion.policy_version_id);

        const requestBody: PolicyVersionBase = {
            alias: policyVersion.alias || null,
            spec: spec ?? policyVersion.workflow?.spec,
            requirements: policyVersion.workflow?.requirements || [],
            ui_metadata: uiMetadata ?? policyVersion.workflow?.ui_metadata,
        };

        const response = await fetch(
            `${serverUrl}/policy-versions/${policyVersion.policy_version_id}`,
            {
                method: "PUT",
                headers: { 
                    "Content-Type": "application/json",
                    ...(isAutoSave && { "X-Auto-Save": "true" }), // Optional header for backend optimization
                },
                body: JSON.stringify(requestBody),
                cache: "no-store",
            },
        );

        if (!response.ok) {
            const error = await response.json();
            const errorMessage = isAutoSave 
                ? `Auto-save failed: ${error.detail || response.statusText}`
                : `Server error ${response.status}: ${error.detail}`;
            
            return apiResponse.error(
                response.status !== 500 ? errorMessage : "Internal server error",
                response.status,
            );
        }

        const data = await response.json();
        return apiResponse.success(data);
    } catch (error) {
        const errorMessage = isAutoSave ? "Auto-save failed" : "Failed to save policy version";
        return apiResponse.error(
            error instanceof Error ? error.message : errorMessage,
        );
    }
}
