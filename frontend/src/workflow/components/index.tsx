import { TransformNode } from "./transform-node";
import { BranchNode } from "./branch-node";
import { TerminateNode } from "./terminate-node";
import { InputNode } from "./input-node";
import { DataInputNode } from "./data-input-node";
import { PolicyNode } from "./policy-node";
import { ConnectionNode } from "./connection-node";
import { DecisionNode } from "./decision-node";

export const nodeTypes = {
    INPUT: InputNode,
    CONNECTION: ConnectionNode,
    DATA_INPUT: DataInputNode,
    TRANSFORM: TransformNode,
    DECISION: DecisionNode,
    BRANCH: BranchNode,
    TERMINATE: TerminateNode,
    POLICY: PolicyNode,
};
