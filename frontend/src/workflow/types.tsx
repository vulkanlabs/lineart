import { type Node } from "@xyflow/react";
import { iconMapping } from "./icons";

export type NodeConfig = {
    id: string;
    name: string;
    icon?: keyof typeof iconMapping;
    height?: number;
    width?: number;
};

export type VulkanNodeData = {
    name?: string;
    icon?: keyof typeof iconMapping;
    minHeight?: number;
    minWidth?: number;
    metadata?: any;
};

export type VulkanNode =
    | Node<VulkanNodeData, "input-node">
    | Node<VulkanNodeData, "connection-node">
    | Node<VulkanNodeData, "data-source-node">
    | Node<VulkanNodeData, "transform-node">
    | Node<VulkanNodeData, "branch-node">
    | Node<VulkanNodeData, "terminate-node">;

export type VulkanNodeType = NonNullable<VulkanNode["type"]>;

export type NodeDependency = {
    node: string;
    output?: string | null;
    key?: string | null;
};

export type GenericNodeDefinition<MetadataType> = {
    name: string;
    node_type: string;
    // description: string;
    metadata?: MetadataType;
    dependencies?: NodeDependency[];
};

export type TerminateNodeMetadata = {
    returnStatus: string;
};

export type TransformNodeMetadata = {
    sourceCode: string;
};

export type BranchNodeMetadata = {
    sourceCode: string;
    choices: string[];
};

export type NodeDefinition = GenericNodeDefinition<
    TerminateNodeMetadata | TransformNodeMetadata | BranchNodeMetadata
>;

export type GraphDefinition = {
    [key: string]: NodeDefinition;
};
