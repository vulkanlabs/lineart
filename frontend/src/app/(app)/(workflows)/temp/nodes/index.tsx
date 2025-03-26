import { useCallback } from "react";
import { Play, Link, ArrowRightFromLine, Split, ArrowDown01, Code2 } from "lucide-react";
import { Node, NodeProps, Handle, Position, XYPosition } from "@xyflow/react";
import { nanoid } from "nanoid";

import { BaseNode } from "@/components/flow/base-node";
import { BaseHandle } from "@/components/flow/base-handle";
import {
    NodeHeaderTitle,
    NodeHeader,
    NodeHeaderActions,
    NodeHeaderAction,
    NodeHeaderMenuAction,
    NodeHeaderDeleteAction,
    NodeHeaderIcon,
} from "@/components/flow/node-header";
// import { NODE_SIZE, WorkflowNodeData } from "@/components/nodes/";
// import { iconMapping } from "@/data/icon-mapping";
// import { NodeStatusIndicator } from "@/components/node-status-indicator";

export const iconMapping = {
    Link: Link,
    Code2: Code2,
    Split: Split,
    ArrowDown01: ArrowDown01,
    ArrowRightFromLine: ArrowRightFromLine,
};

export type WorkflowNodeData = {
    title?: string;
    label?: string;
    icon?: keyof typeof iconMapping;
    status?: "loading" | "success" | "error" | "initial";
};

export const NODE_SIZE = { width: 260, height: 50 };

const HANDLE_STYLE = {
    width: 11,
    height: 11,
    borderRadius: "9999px",
    borderWidth: "1px",
    borderColor: "#cbd5e1",
    backgroundColor: "#f1f5f9",
};

// This is an example of how to implement the WorkflowNode component. All the nodes in the Workflow Builder example
// are variations on this CustomNode defined in the index.tsx file.
// You can also create new components for each of your nodes for greater flexibility.
function WorkflowNode({
    id,
    data,
    children,
    selected,
    isOutput,
}: {
    id: string;
    // data: WorkflowNodeData;
    data: any;
    children?: React.ReactNode;
    selected?: boolean;
    isOutput?: boolean;
}) {
    const onClick = useCallback(() => {}, []);

    const IconComponent = data?.icon ? iconMapping[data.icon] : undefined;

    return (
        // <NodeStatusIndicator status={data?.status}>
        <BaseNode selected={selected} className="p-1" style={{ ...NODE_SIZE }}>
            <NodeHeader>
                <NodeHeaderIcon>
                    {IconComponent ? <IconComponent aria-label={data?.icon} /> : null}
                </NodeHeaderIcon>
                <NodeHeaderTitle className="overflow-hidden whitespace-nowrap text-ellipsis">
                    {data?.title}
                </NodeHeaderTitle>
                <NodeHeaderActions>
                    <NodeHeaderAction onClick={onClick} label="Run node">
                        <Play className="stroke-blue-500 fill-blue-500" />
                    </NodeHeaderAction>
                    <NodeHeaderDeleteAction />
                </NodeHeaderActions>
            </NodeHeader>
            <BaseHandle type="target" position={Position.Top} style={{ ...HANDLE_STYLE }} />
            {isOutput ?? (
                <BaseHandle type="source" position={Position.Bottom} style={{ ...HANDLE_STYLE }} />
            )}
            {children}
        </BaseNode>
        // </NodeStatusIndicator>
    );
}

// export default WorkflowNode;

export function ConnectionNode({ id, data, selected }) {
    return <WorkflowNode id={id} selected={selected} data={data}></WorkflowNode>;
}

export function DataSourceNode({ id, data, selected }) {
    return <WorkflowNode id={id} selected={selected} data={data}></WorkflowNode>;
}

export function TransformNode({ id, data, selected }) {
    return <WorkflowNode id={id} selected={selected} data={data}></WorkflowNode>;
}

export function BranchNode({ id, data, selected }) {
    return <WorkflowNode id={id} selected={selected} data={data}></WorkflowNode>;
}

export function TerminateNode({ id, data, selected }) {
    return <WorkflowNode id={id} selected={selected} data={data} isOutput></WorkflowNode>;
}

export function InputNode({ id, data, selected }) {
    return (
        <div
            style={{ ...NODE_SIZE, backgroundColor: "black", color: "white" }}
            // We add this class to use the same styles as React Flow's default nodes.
            className="react-flow__node-default"
        >
            <div>Input</div>
            <BaseHandle type="source" position={Position.Bottom} style={{ ...HANDLE_STYLE }} />
        </div>
    );
}

export const nodesConfig = {
    "input-node": {
        id: "input-node",
        title: "Input Node",
        handles: [],
        icon: null,
    },
    "connection-node": {
        id: "connection-node",
        title: "Connection Node",
        handles: [],
        icon: "Link",
    },
    "data-source-node": {
        id: "data-source-node",
        title: "Data Source Node",
        handles: [],
        icon: "ArrowDown01",
    },
    "transform-node": {
        id: "transform-node",
        title: "Transform Node",
        handles: [],
        icon: "Code2",
    },
    "branch-node": {
        id: "branch-node",
        title: "Branch Node",
        handles: [],
        icon: "Split",
    },
    "terminate-node": {
        id: "terminate-node",
        title: "Terminate Node",
        handles: [],
        icon: "ArrowRightFromLine",
    },
};

export const nodeTypes = {
    "input-node": InputNode,
    "connection-node": ConnectionNode,
    "data-source-node": DataSourceNode,
    "transform-node": TransformNode,
    "branch-node": BranchNode,
    "terminate-node": TerminateNode,
};

export function createNodeByType({
    type,
    id,
    position = { x: 0, y: 0 },
    data,
}: {
    type: AppNodeType;
    id?: string;
    position?: XYPosition;
    data?: WorkflowNodeData;
}): AppNode {
    const node = nodesConfig[type];

    const newNode: AppNode = {
        id: id ?? nanoid(),
        data: data ?? {
            title: node.title,
            // status: node.status,
            icon: node.icon,
        },
        position: {
            x: position.x - NODE_SIZE.width * 0.5,
            y: position.y - NODE_SIZE.height * 0.5,
        },
        type,
    };

    return newNode;
}

export type AppNode =
    | Node<WorkflowNodeData, "input-node">
    | Node<WorkflowNodeData, "connection-node">
    | Node<WorkflowNodeData, "data-source-node">
    | Node<WorkflowNodeData, "transform-node">
    | Node<WorkflowNodeData, "branch-node">
    | Node<WorkflowNodeData, "terminate-node">;

export type AppNodeType = NonNullable<AppNode["type"]>;
