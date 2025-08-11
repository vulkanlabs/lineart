"use client";

import { useCallback, useState, type ChangeEvent, type FocusEvent } from "react";
import { Play, FoldVertical, UnfoldVertical, PanelRight } from "lucide-react";
import { Position, NodeResizer } from "@xyflow/react";
import { useShallow } from "zustand/react/shallow";

import {
    BaseNode,
    BaseHandle,
    NodeHeaderTitle,
    NodeHeader,
    NodeHeaderActions,
    NodeHeaderAction,
    NodeHeaderDeleteAction,
    NodeHeaderIcon,
} from "@vulkanlabs/base/ui";
import { Button, Input } from "@vulkanlabs/base/ui";

import { useWorkflowStore } from "@/workflow/store";
import { iconMapping } from "@/workflow/icons";
import { standardizeNodeName } from "@/workflow/utils/names";
import type { IncomingEdges } from "@/workflow/types/workflow";

/**
 * Default style for node handles
 */
export const defaultHandleStyle = {
    width: 12,
    height: 12,
    borderRadius: "9999px",
    borderWidth: "1px",
    borderColor: "#cbd5e1",
    backgroundColor: "#f1f5f9",
};

/**
 * Base props for all workflow node components
 */
export type BaseWorkflowNodeProps = {
    id: string;
    data: any;
    width?: number;
    height?: number;
    selected?: boolean;
    isInput?: boolean;
    isOutput?: boolean;
    resizable?: boolean;
    children?: React.ReactNode;
};

/**
 * Props for standard workflow nodes (with input toggle)
 */
export type StandardWorkflowNodeProps = BaseWorkflowNodeProps & {
    showInputsToggle?: boolean;
};

/**
 * Props for input workflow nodes
 */
export type InputWorkflowNodeProps = BaseWorkflowNodeProps;

/**
 * Props for terminate workflow nodes
 */
export type TerminateWorkflowNodeProps = BaseWorkflowNodeProps;

/**
 * Internal props for the base workflow node core
 */
type BaseWorkflowNodeCoreProps = BaseWorkflowNodeProps & {
    headerActions: React.ReactNode;
    footerContent?: React.ReactNode;
    allowNameEditing?: boolean;
};

/**
 * Core base component with shared functionality for all workflow nodes
 */
function BaseWorkflowNodeCore({
    id,
    data,
    width,
    height,
    selected,
    isInput,
    isOutput,
    children,
    resizable,
    headerActions,
    footerContent,
    allowNameEditing = true,
}: BaseWorkflowNodeCoreProps) {
    const [isNameEditing, setIsNameEditing] = useState(false);
    const [showTooltip, setShowTooltip] = useState(false);

    const { updateNodeData, updateTargetDeps, toggleNodeDetails } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            updateTargetDeps: state.updateTargetDeps,
            toggleNodeDetails: state.toggleNodeDetails,
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
        console.log(id);
    }, [id]);

    const toggleDetails = () => {
        toggleNodeDetails(id);
    };

    const toggleNameEditor = useCallback(() => {
        if (!allowNameEditing) {
            setShowTooltip(true);
            setTimeout(() => setShowTooltip(false), 2000);
            return;
        }
        setIsNameEditing((prev) => !prev);
    }, [allowNameEditing]);

    const IconComponent = data?.icon
        ? iconMapping[data.icon as keyof typeof iconMapping]
        : undefined;
    const isExpanded = data.detailsExpanded ?? true;

    return (
        <>
            {resizable && (
                <NodeResizer
                    nodeId={id}
                    color="#ff0071"
                    isVisible={selected}
                    minWidth={data.minWidth}
                    minHeight={data.minHeight}
                />
            )}
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
                            <NodeHeaderAction
                                onClick={openPanel}
                                label="Open Panel"
                                style={{ display: "none" }}
                            >
                                <PanelRight />
                            </NodeHeaderAction>
                            <NodeHeaderAction onClick={toggleDetails} label="Toggle Details">
                                {(data.detailsExpanded ?? true) ? (
                                    <FoldVertical />
                                ) : (
                                    <UnfoldVertical />
                                )}
                            </NodeHeaderAction>
                            {headerActions}
                            {!isInput && <NodeHeaderDeleteAction />}
                        </NodeHeaderActions>
                    </NodeHeader>
                    {isExpanded && <div className="flex-grow min-h-0">{children}</div>}
                    {isExpanded && footerContent}
                </div>
                {!isInput && (
                    <BaseHandle
                        type="target"
                        position={Position.Left}
                        style={{
                            ...defaultHandleStyle,
                            top: "50%",
                            transform: "translateY(-50%)",
                        }}
                    />
                )}
                {!isOutput && (
                    <BaseHandle
                        type="source"
                        position={Position.Right}
                        style={{
                            ...defaultHandleStyle,
                            top: "50%",
                            transform: "translateY(-50%)",
                        }}
                    />
                )}
            </BaseNode>
        </>
    );
}

/**
 * Standard workflow node for most node types
 * Includes play button, inputs toggle, and full functionality
 */
export function StandardWorkflowNode({
    id,
    data,
    width,
    height,
    selected,
    isInput,
    isOutput,
    children,
    resizable,
    showInputsToggle = true,
}: StandardWorkflowNodeProps) {
    const [showInputs, setShowInputs] = useState(false);

    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const handleUpdateDependencyKey = useCallback(
        (edgeId: string, oldKey: string, newKey: string) => {
            if (!newKey || oldKey === newKey) return;

            const dependencies = Object.values(data.incomingEdges as IncomingEdges).reduce(
                (acc, depConfig) => {
                    acc[depConfig.key] = depConfig.dependency;
                    return acc;
                },
                {} as Record<string, any>,
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

    const toggleInputs = () => {
        setShowInputs((prev) => !prev);
    };

    const headerActions = (
        <NodeHeaderAction onClick={() => {}} label="Run node">
            <Play className="stroke-blue-500 fill-blue-500" />
        </NodeHeaderAction>
    );

    const footerContent = showInputsToggle ? (
        <div className="flex gap-1 px-3 py-2 border-t border-slate-200 mt-1">
            <Button variant="outline" size="sm" onClick={toggleInputs}>
                {showInputs ? "Hide Inputs" : "Show Inputs"}
            </Button>
        </div>
    ) : undefined;

    return (
        <>
            <BaseWorkflowNodeCore
                id={id}
                data={data}
                width={width}
                height={height}
                selected={selected}
                isInput={isInput}
                isOutput={isOutput}
                resizable={resizable}
                headerActions={headerActions}
                footerContent={footerContent}
            >
                {children}
            </BaseWorkflowNodeCore>
            {showInputs && (
                <NodeInputs
                    incomingEdges={data.incomingEdges || {}}
                    onUpdateDependencyKey={handleUpdateDependencyKey}
                />
            )}
        </>
    );
}

/**
 * Input workflow node (no name editing, no footer, input only)
 */
export function InputWorkflowNode({
    id,
    data,
    width,
    height,
    selected,
    children,
}: InputWorkflowNodeProps) {
    return (
        <BaseWorkflowNodeCore
            id={id}
            data={data}
            width={width}
            height={height}
            selected={selected}
            isInput={true}
            isOutput={false}
            headerActions={null}
            allowNameEditing={false}
        >
            {children}
        </BaseWorkflowNodeCore>
    );
}

/**
 * Terminate workflow node (not playable, output only, supports footer)
 */
export function TerminateWorkflowNode({
    id,
    data,
    width,
    height,
    selected,
    children,
    footerContent,
}: TerminateWorkflowNodeProps & { footerContent?: React.ReactNode }) {
    return (
        <BaseWorkflowNodeCore
            id={id}
            data={data}
            width={width}
            height={height}
            selected={selected}
            isOutput={true}
            headerActions={null}
            footerContent={footerContent}
        >
            {children}
        </BaseWorkflowNodeCore>
    );
}

/**
 * Legacy export for backwards compatibility
 */
export const WorkflowNode = StandardWorkflowNode;

/**
 * Props for the NodeInputs component
 */
type NodeInputsProps = {
    incomingEdges: IncomingEdges;
    onUpdateDependencyKey: (edgeId: string, oldKey: string, newKey: string) => void;
};

/**
 * Component for displaying and editing node inputs
 */
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
