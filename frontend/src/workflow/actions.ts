"use server";

import { PolicyVersionBase } from "@vulkan-server/PolicyVersionBase";
import { NodeDefinition, NodeMetadata, NodeDependency } from "./types";
import { NodeDefinitionDict } from "@vulkan-server/NodeDefinitionDict";
import { Metadata } from "@vulkan-server/Metadata";
import { DependencyDict } from "@vulkan-server/DependencyDict";

export async function saveWorkflowSpec(policyVersionId: string, nodes: NodeDefinition[]) {
    if (!policyVersionId) {
        throw new Error("Policy version ID is required");
    }
    if (!nodes) {
        throw new Error("Workflow spec is required");
    }
    const nodeDefs = nodes.map((node) => AsNodeDefinitionDict(node));
    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const spec = {
        nodes: nodeDefs,
        input_schema: {
            score: "int",
        },
        output_callable: null,
        config_variables: null,
    };

    console.log("Saving workflow spec:", spec);
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
                console.error(`Server responded with status: ${response.status}: ${response.body}`);
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
        metadata: AsMetadata(node.metadata),
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

function AsMetadata(metadata: NodeMetadata | undefined): Metadata | null {
    if (metadata === null || metadata === undefined) {
        return null;
    }

    // Create a base metadata object
    const baseMetadata: Metadata = {
        schema: {},
        choices: [],
        func: null,
        source_code: "",
        function_code: "",
        return_status: "",
        data_source: "",
        policy_definition: null,
    };

    // Map the specific fields from each node type to the appropriate metadata sections
    if ("return_status" in metadata) {
        // Handle TerminateNodeMetadata
        baseMetadata.return_status = metadata.return_status;
    }

    if ("source_code" in metadata) {
        // Handle TransformNodeMetadata and BranchNodeMetadata
        baseMetadata.source_code = metadata.source_code;

        if (metadata.func) {
            console.warn("`func` is not supported yet. Setting it to null.");
            baseMetadata.func = null;
        }

        // Handle BranchNodeMetadata specific fields
        if ("choices" in metadata && Array.isArray(metadata.choices)) {
            baseMetadata.choices = metadata.choices;
        }
    }

    return baseMetadata;
}
