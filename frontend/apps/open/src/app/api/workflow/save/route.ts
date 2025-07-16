import {
    PolicyVersionBase,
    PolicyDefinitionDictInput,
    UIMetadata,
    PolicyVersion,
    Component,
    ComponentBase,
} from "@vulkanlabs/client-open";
import { updateComponent } from "@/lib/api";
import { Workflow } from "@vulkanlabs/base/workflow";

export async function PUT(request: Request) {
    try {
        const {
            workflow,
            spec,
            uiMetadata,
        }: {
            workflow: Workflow;
            spec: PolicyDefinitionDictInput;
            uiMetadata: { [key: string]: UIMetadata };
        } = await request.json();

        console.log("workflow", workflow);
        console.log("spec", spec);
        console.log("uiMetadata", uiMetadata);

        // Here we handle what type of workflow we are saving.
        // In the future, it'd be nicer to have a single type of workflow that
        // is then managed in many different ways by the backend.
        if (typeof workflow === "object" && "policy_version_id" in workflow) {
            const policyVersion = workflow as PolicyVersion;
            return savePolicyVersion(policyVersion, spec, uiMetadata);
        } else if (typeof workflow === "object" && "component_id" in workflow) {
            const component = workflow as Component;
            return saveComponent(component, spec, uiMetadata);
        } else {
            console.error("Invalid workflow type:", workflow);
            return Response.json(
                { success: false, error: "Invalid workflow type", data: null },
                { status: 400 },
            );
        }
    } catch (error) {
        console.error("Error saving workflow:", error);
        return Response.json(
            {
                success: false,
                error: error instanceof Error ? error.message : "Unknown error",
                data: null,
            },
            { status: 500 },
        );
    }
}

async function saveComponent(
    component: Component,
    spec: PolicyDefinitionDictInput,
    uiMetadata: { [key: string]: UIMetadata },
) {
    if (!spec) {
        return Response.json(
            { success: false, error: "Workflow spec is required", data: null },
            { status: 400 },
        );
    }

    const serverUrl = process.env.VULKAN_SERVER_URL;
    if (!serverUrl) {
        return Response.json(
            { success: false, error: "Server URL is not configured", data: null },
            { status: 500 },
        );
    }

    // Prepare the request body matching the original server action
    const requestBody: ComponentBase = {
        requirements: component.requirements,
        name: component.name,
        description: component.description || null,
        icon: component.icon || null,
        spec,
        input_schema: component.input_schema,
        variables: component.variables || [],
        ui_metadata: uiMetadata,
    };

    const response = await updateComponent(component.component_id, requestBody);
    return Response.json({ success: true, data: response, error: null });
}

async function savePolicyVersion(
    policyVersion: PolicyVersion,
    spec: PolicyDefinitionDictInput,
    uiMetadata: { [key: string]: UIMetadata },
) {
    if (!spec) {
        return Response.json(
            { success: false, error: "Workflow spec is required", data: null },
            { status: 400 },
        );
    }

    const serverUrl = process.env.VULKAN_SERVER_URL;
    if (!serverUrl) {
        return Response.json(
            { success: false, error: "Server URL is not configured", data: null },
            { status: 500 },
        );
    }

    // Prepare the request body matching the original server action
    const requestBody: PolicyVersionBase = {
        alias: policyVersion.alias || null,
        spec,
        requirements: [],
        input_schema: policyVersion.input_schema,
        ui_metadata: uiMetadata,
    };

    // Make the request to the backend server
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
        const error = await response.json();
        if (response.status !== 500) {
            return Response.json(
                {
                    success: false,
                    error: `Server responded with status: ${response.status}: ${error.detail}`,
                    data: null,
                },
                { status: response.status },
            );
        } else {
            console.error(`Server responded with status ${response.status}:`, error);
            return Response.json(
                { success: false, error: "Internal server error", data: null },
                { status: 500 },
            );
        }
    }

    const data = await response.json();
    return Response.json({ success: true, data, error: null });
}
