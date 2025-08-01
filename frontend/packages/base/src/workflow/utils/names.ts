import type { NodeDefinitionDict } from "@vulkanlabs/client-open";
import type { VulkanNode } from "../types/workflow";
import type { BranchNodeMetadata, DecisionNodeMetadata } from "../types/nodes";

/**
 * Standardize a node name by replacing spaces with underscores and converting to lowercase
 */
export function standardizeNodeName(name: string): string {
    return name.replace(/\s+/g, "_").toLowerCase();
}

/**
 * Find the handle name for a given index on a node
 * Used for BRANCH and DECISION nodes that have multiple outputs
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
        return metadata.choices[numericIndex] || "__DEFAULT__";
    } else if (node.type === "DECISION") {
        const metadata = node.data.metadata as DecisionNodeMetadata;
        return metadata.conditions[numericIndex]?.output || null;
    }

    return null;
}

/**
 * Find the handle index for a given name on a node definition
 * Used when converting from server format to client format
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
