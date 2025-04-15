"use server";

import { PolicyVersionBase } from "@vulkan-server/PolicyVersionBase";
import { NodeDefinition, NodeDependency } from "./types";
import { NodeDefinitionDict } from "@vulkan-server/NodeDefinitionDict";
import { DependencyDict } from "@vulkan-server/DependencyDict";
import { UIMetadata } from "@vulkan-server/UIMetadata";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

export async function saveWorkflowSpec(
    policyVersion: PolicyVersion,
    nodes: NodeDefinition[],
    uiMetadata: { [key: string]: UIMetadata },
    inputSchema: { [key: string]: string },
): Promise<{ success: boolean; error: string | null; data: any }> {
    if (!policyVersion || !policyVersion.policy_version_id) {
        throw new Error("Policy version ID is required");
    }
    if (!nodes) {
        throw new Error("Workflow spec is required");
    }

    const nodeDefs = nodes.map((node) => AsNodeDefinitionDict(node));
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const spec = {
        nodes: nodeDefs,
        input_schema: inputSchema,
        output_callable: null,
        config_variables: null,
    };

    const request: PolicyVersionBase = {
        alias: policyVersion.alias,
        spec: spec,
        requirements: [],
        input_schema: inputSchema,
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
                console.error(`Server responded with status: ${response.status}:`, response);
                console.error("Response body:", JSON.stringify(await response.json()));
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

function AsNodeDefinitionDict(node: NodeDefinition): NodeDefinitionDict {
    return {
        name: node.name,
        node_type: node.node_type,
        dependencies: Object.fromEntries(
            Object.entries(node.dependencies).map(([key, value]) => [key, AsDependencyDict(value)]),
        ),
        metadata: node.metadata,
        description: node.description || null,
        hierarchy: node.hierarchy || null,
    };
}

function AsDependencyDict(dependency: NodeDependency): DependencyDict {
    return {
        node: dependency.node,
        output: dependency.output || null,
        key: dependency.key || null,
        hierarchy: null,
    };
}
