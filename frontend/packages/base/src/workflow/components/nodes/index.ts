// Import all node components
import { InputNode } from "./input-node";
import { TransformNode } from "./transform-node";
import { BranchNode } from "./branch-node";
import { DecisionNode } from "./decision-node";
import { TerminateNode } from "./terminate-node";
import { PolicyNode } from "./policy-node";
import { DataInputNode } from "./data-input-node";
import { ConnectionNode } from "./connection-node";
import { ComponentNode } from "./component-node";

// Re-export all node components
export { InputNode } from "./input-node";
export { TransformNode } from "./transform-node";
export { BranchNode } from "./branch-node";
export { DecisionNode } from "./decision-node";
export { TerminateNode } from "./terminate-node";
export { PolicyNode } from "./policy-node";
export { DataInputNode } from "./data-input-node";
export { ConnectionNode } from "./connection-node";

// Base node components
export { StandardWorkflowNode, InputWorkflowNode, TerminateWorkflowNode } from "./base";

// Node types mapping for ReactFlow
export const nodeTypes = {
    INPUT: InputNode,
    CONNECTION: ConnectionNode,
    DATA_INPUT: DataInputNode,
    TRANSFORM: TransformNode,
    DECISION: DecisionNode,
    BRANCH: BranchNode,
    TERMINATE: TerminateNode,
    POLICY: PolicyNode,
    COMPONENT: ComponentNode,
};
