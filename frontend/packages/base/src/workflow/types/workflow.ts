import { type Node, type Edge, type NodeProps } from "@xyflow/react";
import type { NodeDefinitionDict, DependencyDict } from "@vulkanlabs/client-open";

// Re-export commonly used ReactFlow types
export type { Edge, Node, NodeProps } from "@xyflow/react";

/**
 * Configuration for a node type
 */
export type NodeConfig = {
    id: string;
    name: string;
    icon?: string; // Will be mapped to icon components
    height?: number;
    width?: number;
};

/**
 * Map of incoming edges for a node
 */
export type IncomingEdges = {
    [edgeId: string]: {
        key: string;
        dependency: NodeDependency;
    };
};

/**
 * Data structure for Vulkan nodes
 */
export type VulkanNodeData = {
    name?: string;
    icon?: string;
    minHeight?: number;
    minWidth?: number;
    metadata?: any;
    incomingEdges?: IncomingEdges;
    detailsExpanded?: boolean;
    collapsed?: boolean;
};

/**
 * Union type for all Vulkan node types
 */
export type VulkanNode =
    | Node<VulkanNodeData, "INPUT">
    | Node<VulkanNodeData, "CONNECTION">
    | Node<VulkanNodeData, "DATA_INPUT">
    | Node<VulkanNodeData, "TRANSFORM">
    | Node<VulkanNodeData, "BRANCH">
    | Node<VulkanNodeData, "TERMINATE">
    | Node<VulkanNodeData, "POLICY">
    | Node<VulkanNodeData, "DECISION">
    | Node<VulkanNodeData, "COMPONENT">;

/**
 * Extract node type from VulkanNode
 */
export type VulkanNodeType = NonNullable<VulkanNode["type"]>;

/**
 * Props for Vulkan node components (extends ReactFlow NodeProps)
 */
export type VulkanNodeProps = NodeProps<any>;

/**
 * Node dependency structure
 */
export type NodeDependency = {
    node: string;
    output?: string | null;
    key?: string | null;
};

/**
 * Generic node definition structure
 */
export type GenericNodeDefinition<MetadataType> = {
    name: string;
    node_type: string;
    metadata?: MetadataType;
    dependencies?: { [key: string]: NodeDependency };
    description?: string;
    hierarchy?: string[];
};

/**
 * Auto-save state management
 */
export type AutoSaveState = {
    lastSaved: Date | null;
    isSaving: boolean;
    hasUnsavedChanges: boolean;
    saveError: string | null;
    autoSaveEnabled: boolean;
};

/**
 * Main workflow state structure
 */
export type WorkflowState = {
    nodes: VulkanNode[];
    edges: Edge[];
    collapsedNodeHeights?: { [key: string]: number };
    autoSave: AutoSaveState;
};

/**
 * Convert VulkanNode to NodeDefinitionDict for API calls
 */
export function AsNodeDefinitionDict(n: VulkanNode): NodeDefinitionDict {
    const nodeDef = n.data as GenericNodeDefinition<any>;

    return {
        name: nodeDef.name,
        node_type: n.type,
        dependencies: AsDependencies(n.data?.incomingEdges),
        metadata: nodeDef.metadata || null,
        description: nodeDef.description || null,
        hierarchy: nodeDef.hierarchy || null,
    };
}

/**
 * Convert incoming edges to dependencies format
 */
function AsDependencies(incomingEdges: IncomingEdges = {}): { [key: string]: DependencyDict } {
    const deps = Object.values(incomingEdges).reduce(
        (acc, depConfig) => {
            acc[depConfig.key] = AsDependencyDict(depConfig.dependency);
            return acc;
        },
        {} as { [key: string]: DependencyDict },
    );
    return deps;
}

/**
 * Convert NodeDependency to DependencyDict
 */
function AsDependencyDict(dependency: NodeDependency): DependencyDict {
    return {
        node: dependency.node,
        output: dependency.output || null,
        key: dependency.key || null,
        hierarchy: null,
        // expression: null, // TODO: Commented out due to CI/CD TypeScript errors - needs proper type definition
    };
}
