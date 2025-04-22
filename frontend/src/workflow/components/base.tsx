import { useCallback, useState } from "react";
import { Play, FoldVertical, UnfoldVertical, PanelRight } from "lucide-react";
import { Position, NodeResizer } from "@xyflow/react";
import { useShallow } from "zustand/react/shallow";

import { BaseNode } from "@/components/reactflow/base-node";
import { BaseHandle } from "@/components/reactflow/base-handle";
import {
    NodeHeaderTitle,
    NodeHeader,
    NodeHeaderActions,
    NodeHeaderAction,
    NodeHeaderDeleteAction,
    NodeHeaderIcon,
} from "@/components/reactflow/node-header";

import { useWorkflowStore } from "../store";
import { iconMapping } from "../icons";
import { standardizeNodeName } from "../names";

export const defaultHandleStyle = {
    width: 12,
    height: 12,
    borderRadius: "9999px",
    borderWidth: "1px",
    borderColor: "#cbd5e1",
    backgroundColor: "#f1f5f9",
};

type WorkflowNodeProps = {
    id: string;
    data: any;
    width?: number;
    height?: number;
    selected?: boolean;
    isInput?: boolean;
    isOutput?: boolean;
    notPlayable?: boolean;
    disableNameEditing?: boolean;
    children?: React.ReactNode;
};

export function WorkflowNode({
    id,
    data,
    width,
    height,
    selected,
    isInput,
    isOutput,
    notPlayable,
    disableNameEditing,
    children,
}: WorkflowNodeProps) {
    const [isNameEditing, setIsNameEditing] = useState(false);
    const [showDetails, setShowDetails] = useState(true);
    const [showTooltip, setShowTooltip] = useState(false);

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
    };

    const toggleNameEditor = useCallback(() => {
        if (disableNameEditing) {
            // Show temporary tooltip
            setShowTooltip(true);
            setTimeout(() => setShowTooltip(false), 2000);
            return;
        }
        setIsNameEditing((prev) => !prev);
    }, [disableNameEditing]);

    const IconComponent = data?.icon ? iconMapping[data.icon] : undefined;

    return (
        <>
            <NodeResizer
                nodeId={id}
                color="#ff0071"
                isVisible={selected}
                minWidth={data.minWidth}
                minHeight={data.minHeight}
            />
            <BaseNode selected={selected} className="p-1" style={{ width: width, height: height }}>
                <div className="h-full flex flex-col gap-1">
                    <NodeHeader>
                        <NodeHeaderIcon>
                            {IconComponent ? <IconComponent aria-label={data?.icon} /> : null}
                        </NodeHeaderIcon>
                        {isNameEditing ? (
                            <input
                                value={data.name}
                                onChange={(e) => setNodeName(e.target.value)}
                                onBlur={(e) => {
                                    setNodeName(standardizeNodeName(e.target.value));
                                    toggleNameEditor();
                                }}
                                autoFocus
                            />
                        ) : (
                            <div className="relative">
                                <NodeHeaderTitle
                                    onDoubleClick={toggleNameEditor}
                                    className="overflow-hidden whitespace-nowrap text-ellipsis"
                                >
                                    {data.name}
                                </NodeHeaderTitle>
                                {showTooltip && (
                                    <div
                                        className="absolute -top-8 left-0 bg-black 
                                    text-white text-xs px-2 py-1 rounded whitespace-nowrap z-50"
                                    >
                                        You cannot edit this node's name
                                    </div>
                                )}
                            </div>
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
                {isInput ?? (
                    <BaseHandle
                        type="target"
                        position={Position.Left}
                        style={{ ...defaultHandleStyle }}
                    />
                )}
                {isOutput ?? (
                    <BaseHandle
                        type="source"
                        position={Position.Right}
                        style={{ ...defaultHandleStyle }}
                    />
                )}
            </BaseNode>
        </>
    );
}
