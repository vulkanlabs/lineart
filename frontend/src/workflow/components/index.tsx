import { TransformNode } from "./transform-node";
import { BranchNode } from "./branch-node";
import { TerminateNode } from "./terminate-node";
import { InputNode } from "./input-node";
import { ConnectionNode } from "./connection-node";
import { DataSourceNode } from "./data-source-node";

export const nodeTypes = {
    "INPUT": InputNode,
    "CONNECTION": ConnectionNode,
    "DATA_INPUT": DataSourceNode,
    "TRANSFORM": TransformNode,
    "BRANCH": BranchNode,
    "TERMINATE": TerminateNode,
};