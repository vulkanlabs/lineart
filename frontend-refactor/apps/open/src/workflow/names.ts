import { NodeDefinitionDict } from "@vulkan/client-open/models/NodeDefinitionDict";
import { VulkanNode } from "./types";
import { BranchNodeMetadata, DecisionNodeMetadata } from "./types";

export function standardizeNodeName(name: string): string {
    return name.replace(/\s+/g, "_").toLowerCase();
}

export function findHandleNameByIndex(
    node: VulkanNode,
    index: string | number,
): string | undefined {
    if (node === null || node === undefined) {
        return undefined;
    }

    if (typeof index === "string") {
        index = parseInt(index, 10);
    }

    if (node.type === "BRANCH") {
        const metadata = node.data.metadata as BranchNodeMetadata;
        return metadata.choices[index];
    } else if (node.type === "DECISION") {
        const metadata = node.data.metadata as DecisionNodeMetadata;
        return metadata.conditions[index]?.output;
    }
    return undefined;
}

export function findHandleIndexByName(node: NodeDefinitionDict, name: string): number | undefined {
    if (node.node_type === "BRANCH") {
        const metadata = node.metadata as BranchNodeMetadata;
        return metadata.choices.indexOf(name);
    } else if (node.node_type === "DECISION") {
        const metadata = node.metadata as DecisionNodeMetadata;
        return metadata.conditions.findIndex((c) => c.output === name);
    }
    return undefined;
}
