import type { GenericNodeDefinition, NodeDependency } from "./workflow";

// Re-export commonly used types
export type { NodeDependency };

/**
 * Metadata for branch nodes
 */
export type BranchNodeMetadata = {
    source_code: string;
    choices: string[];
};

/**
 * Metadata for data input nodes
 */
export type DataInputNodeMetadata = {
    data_source: string;
};

/**
 * Metadata for input nodes
 */
export type InputNodeMetadata = {
    schema: { [key: string]: string };
};

/**
 * Metadata for terminate nodes
 */
export type TerminateNodeMetadata = {
    return_status: string;
    return_metadata?: string;
};

/**
 * Metadata for transform nodes
 */
export type TransformNodeMetadata = {
    source_code: string;
};

/**
 * Metadata for policy definition nodes
 */
export type PolicyDefinitionNodeMetadata = {
    policy_id: string;
};

/**
 * Decision condition structure
 */
export type DecisionCondition = {
    decision_type: "if" | "else-if" | "else";
    condition?: string; // Jinja2 template string for 'if' and 'else-if'
    output: string;
};

/**
 * Metadata for decision nodes
 */
export type DecisionNodeMetadata = {
    conditions: DecisionCondition[];
};

/**
 * Union type for all node metadata types
 */
export type NodeMetadata =
    | BranchNodeMetadata
    | DataInputNodeMetadata
    | TerminateNodeMetadata
    | TransformNodeMetadata
    | PolicyDefinitionNodeMetadata
    | DecisionNodeMetadata
    | InputNodeMetadata;

/**
 * Complete node definition with typed metadata
 */
export type NodeDefinition = GenericNodeDefinition<NodeMetadata>;

/**
 * Graph definition as a map of node definitions
 */
export type GraphDefinition = {
    [key: string]: NodeDefinition;
};
