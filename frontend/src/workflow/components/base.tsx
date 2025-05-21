import { useCallback, useState, ChangeEvent, FocusEvent } from "react";
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { useWorkflowStore } from "../store";
import { iconMapping } from "../icons";
import { standardizeNodeName } from "../names";
import { type IncomingEdges } from "../types";

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
    disableFooter?: boolean;
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
    disableFooter,
    children,
}: WorkflowNodeProps) {
    const [isNameEditing, setIsNameEditing] = useState(false);
    const [showDetails, setShowDetails] = useState(true);
    const [showTooltip, setShowTooltip] = useState(false);
    const [showInputs, setShowInputs] = useState(false);

    const { updateNodeData, updateTargetDeps } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            updateTargetDeps: state.updateTargetDeps,
        })),
    );
    const setNodeName = useCallback(
        (name: string) => {
            updateNodeData(id, { ...data, name: name });
            updateTargetDeps(id);
        },
        [id, data, updateNodeData, updateTargetDeps],
    );

    const openPanel = useCallback(() => {
        // openPanel(id);
        console.log(id);
    }, [id]);

    const toggleDetails = () => {
        setShowDetails((prev) => !prev);
    };

    const toggleInputs = () => {
        setShowInputs((prev) => !prev);
    };

    const toggleNameEditor = useCallback(() => {
        if (disableNameEditing) {
            setShowTooltip(true);
            setTimeout(() => setShowTooltip(false), 2000);
            return;
        }
        setIsNameEditing((prev) => !prev);
    }, [disableNameEditing]);

    const handleUpdateDependencyKey = useCallback(
        (edgeId: string, oldKey: string, newKey: string) => {
            if (!newKey || oldKey === newKey) return;

            const dependencies = Object.values(data.incomingEdges as IncomingEdges).reduce(
                (acc, depConfig) => {
                    acc[depConfig.key] = depConfig.dependency;
                    return acc;
                },
                {},
            );
            if (dependencies[oldKey] && !dependencies[newKey]) {
                const depConfig = { ...data.incomingEdges[edgeId] };
                depConfig.key = newKey;
                updateNodeData(id, {
                    ...data,
                    incomingEdges: { ...data.incomingEdges, [edgeId]: depConfig },
                });
            } else {
                console.warn(
                    `Cannot rename dependency key: "${newKey}" might already exist or is invalid.`,
                );
            }
        },
        [id, data, updateNodeData],
    );

    const IconComponent = data?.icon ? iconMapping[data.icon] : undefined;

    return (
        <>
            {/* TODO: use a custom icon for resizer */}
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
                            <div
                                className="flex-grow min-w-0 nodrag"
                                onMouseDown={(e) => e.stopPropagation()}
                            >
                                <input
                                    value={data.name}
                                    onChange={(e) => setNodeName(e.target.value)}
                                    onBlur={(e) => {
                                        setNodeName(standardizeNodeName(e.target.value));
                                        toggleNameEditor();
                                    }}
                                    autoFocus
                                    className="bg-transparent border rounded px-1 w-full"
                                />
                            </div>
                        ) : (
                            <div className="relative flex-grow min-w-0">
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
                                        {"You cannot edit this node's name"}
                                    </div>
                                )}
                            </div>
                        )}
                        <NodeHeaderActions>
                            <NodeHeaderAction onClick={openPanel} label="Open Panel">
                                <PanelRight />
                            </NodeHeaderAction>
                            <NodeHeaderAction onClick={toggleDetails} label="Toggle Details">
                                {showDetails ? <FoldVertical /> : <UnfoldVertical />}
                            </NodeHeaderAction>
                            {!notPlayable && (
                                <NodeHeaderAction onClick={() => {}} label="Run node">
                                    <Play className="stroke-blue-500 fill-blue-500" />
                                </NodeHeaderAction>
                            )}
                            <NodeHeaderDeleteAction />
                        </NodeHeaderActions>
                    </NodeHeader>
                    {showDetails && <div className="flex-grow min-h-0">{children}</div>}
                    {!disableFooter && (
                        <div className="flex gap-1 px-3 py-2 border-t border-slate-200 mt-1">
                            <Button variant="outline" size="sm" onClick={toggleInputs}>
                                {showInputs ? "Hide Inputs" : "Show Inputs"}
                            </Button>
                        </div>
                    )}
                </div>
                {!isInput && (
                    <BaseHandle
                        type="target"
                        position={Position.Left}
                        style={{ ...defaultHandleStyle }}
                    />
                )}
                {!isOutput && (
                    <BaseHandle
                        type="source"
                        position={Position.Right}
                        style={{ ...defaultHandleStyle }}
                    />
                )}
            </BaseNode>
            {showInputs && (
                <NodeInputs
                    incomingEdges={data.incomingEdges || {}}
                    onUpdateDependencyKey={handleUpdateDependencyKey}
                />
            )}
        </>
    );
}

type NodeInputsProps = {
    incomingEdges: IncomingEdges;
    onUpdateDependencyKey: (edgeId: string, oldKey: string, newKey: string) => void;
};

function NodeInputs({ incomingEdges, onUpdateDependencyKey }: NodeInputsProps) {
    const [editingKey, setEditingKey] = useState<string | null>(null);
    const [currentValue, setCurrentValue] = useState<string>("");

    const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
        setCurrentValue(event.target.value);
    };

    const handleInputBlur = (
        event: FocusEvent<HTMLInputElement>,
        edgeId: string,
        oldKey: string,
    ) => {
        const newKey = event.target.value.trim();
        if (editingKey === oldKey) {
            onUpdateDependencyKey(edgeId, oldKey, newKey);
        }
        setEditingKey(null);
    };

    const handleInputKeyDown = (
        event: React.KeyboardEvent<HTMLInputElement>,
        edgeId: string,
        oldKey: string,
    ) => {
        if (event.key === "Enter") {
            const newKey = (event.target as HTMLInputElement).value.trim();
            onUpdateDependencyKey(edgeId, oldKey, newKey);
            setEditingKey(null);
            event.currentTarget.blur();
        } else if (event.key === "Escape") {
            setEditingKey(null);
            event.currentTarget.blur();
        }
    };

    const startEditing = (key: string) => {
        setEditingKey(key);
        setCurrentValue(key);
    };

    return (
        <div className="bg-slate-50 border border-slate-200 rounded shadow-sm mt-2 p-3 w-full">
            <h4 className="text-sm font-semibold mb-2 text-slate-600">Node Inputs</h4>
            {Object.keys(incomingEdges).length === 0 ? (
                <p className="text-xs text-slate-500">No inputs connected.</p>
            ) : (
                <div className="space-y-2">
                    <div className="grid grid-cols-2 gap-2 text-xs font-medium text-slate-500 px-1">
                        <span>Variable</span>
                        <span>Source Node</span>
                    </div>
                    {Object.entries(incomingEdges).map(([edgeId, { key, dependency }]) => (
                        <div key={edgeId} className="grid grid-cols-2 gap-2 items-center text-sm">
                            {editingKey === key ? (
                                <div className="nodrag" onMouseDown={(e) => e.stopPropagation()}>
                                    <Input
                                        type="text"
                                        value={currentValue}
                                        onChange={handleInputChange}
                                        onBlur={(e) => handleInputBlur(e, edgeId, key)}
                                        onKeyDown={(e) => handleInputKeyDown(e, edgeId, key)}
                                        autoFocus
                                        className="h-7 text-sm"
                                    />
                                </div>
                            ) : (
                                <span
                                    className="px-1 py-0.5 rounded hover:bg-slate-200 cursor-pointer truncate"
                                    onDoubleClick={() => startEditing(key)}
                                    title={`Double-click to edit "${key}"`}
                                >
                                    {key}
                                </span>
                            )}
                            <span className="text-slate-700 truncate px-1" title={dependency.node}>
                                {dependency.node}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
