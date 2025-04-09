import { type Node, type Edge } from "@xyflow/react";
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
    | Node<VulkanNodeData, "INPUT">
    | Node<VulkanNodeData, "CONNECTION">
    | Node<VulkanNodeData, "DATA_INPUT">
    | Node<VulkanNodeData, "TRANSFORM">
    | Node<VulkanNodeData, "BRANCH">
    | Node<VulkanNodeData, "TERMINATE">;

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
    dependencies?: Map<string, NodeDependency>;
};

export type TerminateNodeMetadata = {
    return_status: string;
};

export type TransformNodeMetadata = {
    source_code: string;
    func?: string | null;
};

export type BranchNodeMetadata = {
    source_code: string;
    func?: string | null;
    choices: string[];
};

export type NodeDefinition = GenericNodeDefinition<
    TerminateNodeMetadata | TransformNodeMetadata | BranchNodeMetadata
>;

export type GraphDefinition = {
    [key: string]: NodeDefinition;
};

export type WorkflowState = {
    nodes: VulkanNode[];
    edges: Edge[];
};
