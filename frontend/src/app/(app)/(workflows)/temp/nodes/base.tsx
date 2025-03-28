import { useCallback, useState } from "react";
import { Play, Link, ArrowRightFromLine, Split, ArrowDown01, Code2 } from "lucide-react";
import { Node, NodeProps, Handle, Position, XYPosition, NodeResizer } from "@xyflow/react";

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

import { iconMapping } from "./icons";

export const NODE_SIZE = { width: 260, height: 50 };

export const HANDLE_STYLE = {
    width: 11,
    height: 11,
    borderRadius: "9999px",
    borderWidth: "1px",
    borderColor: "#cbd5e1",
    backgroundColor: "#f1f5f9",
};

export function WorkflowNode({
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
