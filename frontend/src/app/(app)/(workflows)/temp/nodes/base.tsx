import { useCallback, useState } from "react";
import { Play, FoldVertical, UnfoldVertical, PanelRight } from "lucide-react";
import { Node, NodeProps, Position, XYPosition, NodeResizer } from "@xyflow/react";
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
import { cn } from "@/lib/utils";

import { useWorkflowStore } from "../store";
import { iconMapping } from "./icons";

export const NODE_SIZE = { width: 350, height: 50 };

export const HANDLE_STYLE = {
    width: 12,
    height: 12,
    borderRadius: "9999px",
    borderWidth: "1px",
    borderColor: "#cbd5e1",
    backgroundColor: "#f1f5f9",
};

export function WorkflowNode({
    id,
    data,
    width,
    height,
    selected,
    isOutput,
    notPlayable,
    children,
}: {
    id: string;
    // data: WorkflowNodeData;
    data: any;
    width?: number;
    height?: number;
    selected?: boolean;
    isOutput?: boolean;
    notPlayable?: boolean;
    children?: React.ReactNode;
}) {
    const [isNameEditing, setIsNameEditing] = useState(false);
    const [showDetails, setShowDetails] = useState(true);

    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );
    const setNodeName = useCallback(
        (name: string) => {
            updateNodeData(id, { ...data, name: name });
        },
        [id, data, updateNodeData],
    );

    const openPanel = useCallback(() => {
        // openPanel(id);
    }, [id]);

    const toggleDetails = () => {
        setShowDetails((prev) => !prev);
        // onNodesChange([
        //     {
        //         id: id,
        //         type: "dimensions",
        //         resizing: true,
        //         setAttributes: true,
        //         dimensions: {
        //             width: width,
        //             height: newHeight,
        //         },
        //     },
        // ] as NodeChange<VulkanNode>[]);
    };

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
                <div className="h-full flex flex-col gap-1">
                    <NodeHeader>
                        <NodeHeaderIcon>
                            {IconComponent ? <IconComponent aria-label={data?.icon} /> : null}
                        </NodeHeaderIcon>
                        {isNameEditing ? (
                            <input
                                value={data.name}
                                onChange={(e) => setNodeName(e.target.value)}
                                onBlur={toggleNameEditor}
                                autoFocus
                            />
                        ) : (
                            <NodeHeaderTitle
                                onDoubleClick={toggleNameEditor}
                                className="overflow-hidden whitespace-nowrap text-ellipsis"
                            >
                                {data.name}
                            </NodeHeaderTitle>
                        )}
                        <NodeHeaderActions>
                            <NodeHeaderAction onClick={openPanel} label="Fold/Unfold">
                                <PanelRight />
                            </NodeHeaderAction>
                            <NodeHeaderAction onClick={toggleDetails} label="Fold/Unfold">
                                {showDetails ? <FoldVertical /> : <UnfoldVertical />}
                            </NodeHeaderAction>
                            {notPlayable ?? (
                                <NodeHeaderAction onClick={() => {}} label="Run node">
                                    <Play className="stroke-blue-500 fill-blue-500" />
                                </NodeHeaderAction>
                            )}
                            <NodeHeaderDeleteAction />
                        </NodeHeaderActions>
                    </NodeHeader>
                    {showDetails && children}
                </div>
                <BaseHandle type="target" position={Position.Left} style={{ ...HANDLE_STYLE }} />
                {isOutput ?? (
                    <BaseHandle
                        type="source"
                        position={Position.Right}
                        style={{ ...HANDLE_STYLE }}
                    />
                )}
            </BaseNode>
        </>
        // </NodeStatusIndicator>
    );
}

// export default WorkflowNode;
