import {
    PolicyVersionBase,
    PolicyVersion,
    PolicyDefinitionDictInput,
    UIMetadata,
} from "@vulkan/client-open";

export async function PUT(request: Request) {
    try {
        const {
            policyVersion,
            spec,
            uiMetadata,
        }: {
            policyVersion: PolicyVersion;
            spec: PolicyDefinitionDictInput;
            uiMetadata: { [key: string]: UIMetadata };
        } = await request.json();

        // Validation
        if (!policyVersion || !policyVersion.policy_version_id) {
            return Response.json(
                { success: false, error: "Policy version ID is required", data: null },
                { status: 400 },
            );
        }

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
            alias: policyVersion.alias,
            spec: spec,
            requirements: [],
            input_schema: spec.input_schema,
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
