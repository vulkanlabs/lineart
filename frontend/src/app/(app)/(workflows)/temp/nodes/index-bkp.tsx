import { useCallback, useState } from "react";
import { Play, Link, ArrowRightFromLine, Split, ArrowDown01, Code2 } from "lucide-react";
import { Node, NodeProps, Handle, Position, XYPosition, NodeResizer } from "@xyflow/react";
import { nanoid } from "nanoid";
import Editor from "@monaco-editor/react";
import { useShallow } from "zustand/react/shallow";

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
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { useWorkflowStore } from "../store";

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
    // icon?: keyof typeof iconMapping;
    icon?: string;
    minHeight?: number;
    minWidth?: number;
    metadata?: any;
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

function WorkflowNode({
    id,
    data,
    height,
    width,
    selected,
    isOutput,
    children,
}: {
    id: string;
    // data: WorkflowNodeData;
    data: any;
    height?: number;
    width?: number;
    selected?: boolean;
    isOutput?: boolean;
    children?: React.ReactNode;
}) {
    const [isNameEditing, setIsNameEditing] = useState(false);
    const [nodeName, setNodeName] = useState(data?.title ?? "New Node");
    const onClick = useCallback(() => {}, []);

    const toggleNameEditor = useCallback(() => {
        setIsNameEditing((prev) => !prev);
    }, []);

    const IconComponent = data?.icon ? iconMapping[data.icon] : undefined;

    return (
        // <NodeStatusIndicator status={data?.status}>
        <>
            <NodeResizer
                nodeId={id}
                color="#ff0071"
                isVisible={selected}
                minWidth={data.minWidth}
                minHeight={data.minHeight}
            />
            <BaseNode
                selected={selected}
                className="p-1"
                style={{
                    width: width ?? NODE_SIZE.width,
                    height: height ?? NODE_SIZE.height,
                }}
            >
                <NodeHeader>
                    <NodeHeaderIcon>
                        {IconComponent ? <IconComponent aria-label={data?.icon} /> : null}
                    </NodeHeaderIcon>
                    {isNameEditing ? (
                        <input
                            value={nodeName}
                            onChange={(e) => setNodeName(e.target.value)}
                            onBlur={toggleNameEditor}
                            autoFocus
                        />
                    ) : (
                        <NodeHeaderTitle
                            onDoubleClick={toggleNameEditor}
                            className="overflow-hidden whitespace-nowrap text-ellipsis"
                        >
                            {nodeName}
                        </NodeHeaderTitle>
                    )}
                    <NodeHeaderActions>
                        <NodeHeaderAction onClick={onClick} label="Run node">
                            <Play className="stroke-blue-500 fill-blue-500" />
                        </NodeHeaderAction>
                        <NodeHeaderDeleteAction />
                    </NodeHeaderActions>
                </NodeHeader>
                <BaseHandle type="target" position={Position.Top} style={{ ...HANDLE_STYLE }} />
                {isOutput ?? (
                    <BaseHandle
                        type="source"
                        position={Position.Bottom}
                        style={{ ...HANDLE_STYLE }}
                    />
                )}
                {children}
            </BaseNode>
        </>
        // </NodeStatusIndicator>
    );
}

// export default WorkflowNode;

export function ConnectionNode({ id, data, selected, height, width }) {
    return (
        <WorkflowNode
            id={id}
            selected={selected}
            data={data}
            height={height}
            width={width}
        ></WorkflowNode>
    );
}

export function DataSourceNode({ id, data, selected, height, width }) {
    return (
        <WorkflowNode
            id={id}
            selected={selected}
            data={data}
            height={height}
            width={width}
        ></WorkflowNode>
    );
}

const CodeEditorWindow = ({ onChange, language, code, theme, height, width }) => {
    const [value, setValue] = useState(code || "");

    const handleEditorChange = (value) => {
        setValue(value);
        onChange("code", value);
    };

    return (
        // <div className="rounded-md overflow-hidden m-3">
        <Editor
            // height={height}
            // width={width}
            language={language || "javascript"}
            value={value}
            theme={theme}
            defaultValue="// some comment"
            onChange={handleEditorChange}
        />
        // </div>
    );
};

export function TransformNode({ id, data, selected, height, width }) {
    const [code, setCode] = useState("");

    return (
        <WorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            {/* <CodeEditorWindow
                onChange={() => {}}
                language="javascript"
                code={""}
                theme="vs-dark"
                height={height}
                width={width}
            /> */}
            <Textarea value={code} onChange={(e) => setCode(e.target.value)} />
        </WorkflowNode>
    );
}

export function BranchNode({ id, data, selected, height, width }) {
    return (
        <WorkflowNode
            id={id}
            selected={selected}
            data={data}
            height={height}
            width={width}
        ></WorkflowNode>
    );
}

export function TerminateNode({ id, data, selected, height, width }) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    // const setReturnStatus = useCallback(
    //     (status: string) => {
    //         updateNodeData(id, { ...data, metadata: { returnStatus: status } });
    //     },
    //     [id, data, updateNodeData],
    // );

    return (
        <WorkflowNode
            id={id}
            selected={selected}
            data={data}
            height={height}
            width={width}
            isOutput
        >
            <div className="flex flex-col gap-1 space-y-2 p-3">
                <span>Return status:</span>
                <Input
                    type="text"
                    value={data.metadata?.returnStatus}
                    // onChange={(e) => setReturnStatus(e.target.value)}
                />
            </div>
        </WorkflowNode>
    );
}

export function InputNode({ id, data, selected, height, width }) {
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

export type NodeConfig = {
    id: string;
    title: string;
    icon: string;
    height?: number;
    width?: number;
};

export const nodesConfig: Record<VulkanNodeType, NodeConfig> = {
    "input-node": {
        id: "input-node",
        title: "Input Node",
        icon: null,
    },
    "connection-node": {
        id: "connection-node",
        title: "Connection Node",
        icon: "Link",
    },
    "data-source-node": {
        id: "data-source-node",
        title: "Data Source Node",
        icon: "ArrowDown01",
    },
    "transform-node": {
        id: "transform-node",
        title: "Transform Node",
        height: 300,
        width: 600,
        icon: "Code2",
    },
    "branch-node": {
        id: "branch-node",
        title: "Branch Node",
        icon: "Split",
    },
    "terminate-node": {
        id: "terminate-node",
        title: "Terminate Node",
        height: 200,
        width: 400,
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
    type: VulkanNodeType;
    id?: string;
    position?: XYPosition;
    data?: WorkflowNodeData;
}): VulkanNode {
    const node = nodesConfig[type];

    const newNode: VulkanNode = {
        id: id ?? nanoid(),
        data: data ?? {
            title: node.title,
            // status: node.status,
            minHeight: node.height,
            minWidth: node.width,
            icon: node.icon,
        },
        position: {
            x: position.x - NODE_SIZE.width * 0.5,
            y: position.y - NODE_SIZE.height * 0.5,
        },
        height: node.height ?? NODE_SIZE.height,
        width: node.width ?? NODE_SIZE.width,
        type,
    };

    return newNode;
}

export type VulkanNode =
    | Node<WorkflowNodeData, "input-node">
    | Node<WorkflowNodeData, "connection-node">
    | Node<WorkflowNodeData, "data-source-node">
    | Node<WorkflowNodeData, "transform-node">
    | Node<WorkflowNodeData, "branch-node">
    | Node<WorkflowNodeData, "terminate-node">;

export type VulkanNodeType = NonNullable<VulkanNode["type"]>;
