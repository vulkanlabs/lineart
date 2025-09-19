import type { NodeDefinitionDict } from "@vulkanlabs/client-open";
import type { VulkanNode } from "../types/workflow";
import type { BranchNodeMetadata, DecisionNodeMetadata } from "../types/nodes";

/**
 * Standardize a node name for system use
 * @param {string} name - Raw node name from user input
 * @returns {string} Standardized name with underscores and lowercase
 *
 * "My Data Node" → "my_data_node"
 */
export function standardizeNodeName(name: string): string {
    return name.replace(/\s+/g, "_").toLowerCase();
}

/**
 * Get the output handle name for a specific index on branching nodes
 * @param {VulkanNode} node - The workflow node (must be BRANCH or DECISION type)
 * @param {string|number|null} index - Which output handle to get (0, 1, 2, etc.)
 * @returns {string|null} Handle name like "success", "error", "choice_1" or null if not found
 *
 * BRANCH nodes: Returns choice labels like "option_a", "option_b"
 * DECISION nodes: Returns condition outputs like "success", "failure"
 */
export function findHandleNameByIndex(
    node: VulkanNode,
    index: string | number | null,
): string | null {
    if (node === null || node === undefined || index === null) {
        return null;
    }

    let numericIndex: number;
    if (typeof index === "string") {
        numericIndex = parseInt(index, 10);
        if (isNaN(numericIndex)) {
            return null;
        }
    } else {
        numericIndex = index;
    }

    if (node.type === "BRANCH") {
        const metadata = node.data.metadata as BranchNodeMetadata;
        return metadata.choices[numericIndex] ?? "__DEFAULT__";
    } else if (node.type === "DECISION") {
        const metadata = node.data.metadata as DecisionNodeMetadata;
        return metadata.conditions[numericIndex]?.output ?? null;
    }

    return null;
}

/**
 * Reverse lookup: find the index for a given handle name
 * @param {NodeDefinitionDict} node - Node definition from server
 * @param {string} name - Handle name to find index for
 * @returns {number|null} Index (0, 1, 2, etc.) or null if name not found
 */
export function findHandleIndexByName(node: NodeDefinitionDict, name: string): number | null {
    if (node.node_type === "BRANCH") {
        const metadata = node.metadata as BranchNodeMetadata;
        const index = metadata.choices.indexOf(name);
        return index >= 0 ? index : null;
    } else if (node.node_type === "DECISION") {
        const metadata = node.metadata as DecisionNodeMetadata;
        const index = metadata.conditions.findIndex((c) => c.output === name);
        return index >= 0 ? index : null;
    }
    return null;
}
