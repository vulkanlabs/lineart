import { TransformNode } from "./transform-node";
import { BranchNode } from "./branch-node";
import { TerminateNode } from "./terminate-node";
import { InputNode } from "./input-node";
import { ConnectionNode } from "./connection-node";
import { DataSourceNode } from "./data-source-node";

export const nodeTypes = {
    "input-node": InputNode,
    "connection-node": ConnectionNode,
    "data-source-node": DataSourceNode,
    "transform-node": TransformNode,
    "branch-node": BranchNode,
    "terminate-node": TerminateNode,
};