import { type Node, type Edge } from "@xyflow/react";
import { iconMapping } from "./icons";

export type NodeConfig = {
    id: string;
    name: string;
    icon?: keyof typeof iconMapping;
    height?: number;
    width?: number;
};

export type IncomingEdges = { [edgeId: string]: { key: string; dependency: NodeDependency } };

export type VulkanNodeData = {
    name?: string;
    icon?: keyof typeof iconMapping;
    minHeight?: number;
    minWidth?: number;
    metadata?: any;
    incomingEdges?: IncomingEdges;
    detailsExpanded?: boolean;
    collapsed?: boolean;
};

export type DecisionCondition = {
    type: "if" | "else-if" | "else";
    condition?: string; // Jinja2 template string for 'if' and 'else-if'
    output: string; // Name of the output branch
};

export type DecisionNodeMetadata = {
    conditions: DecisionCondition[];
};

export type VulkanNode =
    | Node<VulkanNodeData, "INPUT">
    | Node<VulkanNodeData, "CONNECTION">
    | Node<VulkanNodeData, "DATA_INPUT">
    | Node<VulkanNodeData, "TRANSFORM">
    | Node<VulkanNodeData, "BRANCH">
    | Node<VulkanNodeData, "TERMINATE">
    | Node<VulkanNodeData, "POLICY">
    | Node<VulkanNodeData, "DECISION">;

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
    return_metadata?: { [key: string]: NodeDependency };
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
    | PolicyDefinitionNodeMetadata
    | DecisionNodeMetadata; // Added DecisionNodeMetadata

export type NodeDefinition = GenericNodeDefinition<NodeMetadata>;

export type GraphDefinition = {
    [key: string]: NodeDefinition;
};

export type WorkflowState = {
    nodes: VulkanNode[];
    edges: Edge[];
    collapsedNodeHeights?: { [key: string]: number };
};
