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
    | Node<VulkanNodeData, "TERMINATE">
    | Node<VulkanNodeData, "POLICY">;

export type VulkanNodeType = NonNullable<VulkanNode["type"]>;

export type NodeDependency = {
    node: string;
    output?: string | null;
    key?: string | null;
};

export type GenericNodeDefinition<MetadataType> = {
    name: string;
    node_type: string;
    metadata?: MetadataType;
    dependencies?: { [key: string]: NodeDependency };
    description?: string;
    hierarchy?: string[];
};

export type BranchNodeMetadata = {
    source_code: string;
    choices: string[];
};

export type DataInputNodeMetadata = {
    data_source: string;
};

export type InputNodeMetadata = {
    schema: { [key: string]: string };
};

export type TerminateNodeMetadata = {
    return_status: string;
};

export type TransformNodeMetadata = {
    source_code: string;
};

export type PolicyDefinitionNodeMetadata = {
    policy_id: string;
};

export type NodeMetadata =
    | BranchNodeMetadata
    | DataInputNodeMetadata
    | TerminateNodeMetadata
    | TransformNodeMetadata
    | PolicyDefinitionNodeMetadata;

export type NodeDefinition = GenericNodeDefinition<NodeMetadata>;

export type GraphDefinition = {
    [key: string]: NodeDefinition;
};

export type WorkflowState = {
    nodes: VulkanNode[];
    edges: Edge[];
};
