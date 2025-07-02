import { useCallback } from "react";
import { SquareX } from "lucide-react";
import { useShallow } from "zustand/react/shallow";
import { Position, type NodeChange, NodeProps } from "@xyflow/react";
import Editor from "@monaco-editor/react";

import { Input } from "@vulkan/base/ui";
import { BaseHandle } from "@vulkan/base";
import { Button } from "@vulkan/base/ui";

import { VulkanNode } from "../types";
import { useWorkflowStore } from "../store";
import { StandardWorkflowNode, defaultHandleStyle } from "./base";

export function BranchNode({ id, data, selected, height, width }: NodeProps<VulkanNode>) {
    const { updateNodeData, updateTargetDeps, onNodesChange } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            updateTargetDeps: state.updateTargetDeps,
            onNodesChange: state.onNodesChange,
        })),
    );

    const setSourceCode = useCallback(
        (code: string) => {
            const metadata = { ...data.metadata, source_code: code };
            updateNodeData(id, { ...data, metadata });
        },
        [id, data, updateNodeData],
    );

    const setBranchChoices = useCallback(
        (choices: string[]) => {
            const metadata = { ...data.metadata, choices: choices };
            updateNodeData(id, { ...data, metadata });
            updateTargetDeps(id);
        },
        [id, data, updateNodeData, updateTargetDeps],
    );

    const heightStepSize = 80; // Adjust this value as needed

    const addChoice = useCallback(() => {
        const newHeight = height + heightStepSize;
        const newChoices = [...data.metadata.choices, ""];
        const metadata = { ...data.metadata, choices: newChoices };

        updateNodeData(id, { ...data, metadata, minHeight: newHeight });

        onNodesChange([
            {
                id: id,
                type: "dimensions",
                resizing: true,
                setAttributes: true,
                dimensions: {
                    width: width,
                    height: newHeight,
                },
            },
        ] as NodeChange<VulkanNode>[]);
    }, [id, data, height, width, updateNodeData, onNodesChange]);

    const removeChoice = useCallback(
        (index: number) => {
            const newHeight = height - heightStepSize;
            const newChoices = [...data.metadata.choices];
            newChoices.splice(index, 1);

            const metadata = { ...data.metadata, choices: newChoices };

            updateNodeData(id, { ...data, metadata, minHeight: newHeight });

            // TODO: remove the edge whose source was deleted

            onNodesChange([
                {
                    id: id,
                    type: "dimensions",
                    resizing: true,
                    setAttributes: true,
                    dimensions: {
                        width: width,
                        height: newHeight,
                    },
                },
            ] as NodeChange<VulkanNode>[]);
        },
        [id, data, height, width, updateNodeData, onNodesChange],
    );

    const isExpanded = data.detailsExpanded ?? true;

    return (
        <>
            <StandardWorkflowNode
                id={id}
                selected={selected}
                data={data}
                height={height}
                width={width}
                isOutput
            >
                <div className="h-full flex flex-col gap-1 space-y-2 p-3">
                    <div
                        className="rounded-md overflow-hidden h-full flex-grow nodrag"
                        onMouseDown={(e) => e.stopPropagation()}
                    >
                        <Editor
                            language="python"
                            value={data.metadata?.source_code || ""}
                            theme="vs-dark"
                            defaultValue="# your code here"
                            onChange={(value) => setSourceCode(value || "")}
                            options={{
                                minimap: {
                                    enabled: false,
                                },
                            }}
                        />
                    </div>
                    <span>Outputs:</span>
                    {data.metadata.choices.map((choice, index) => (
                        <div
                            key={index}
                            className="relative flex flex-row items-center gap-2 p-2 pr-4 border 
                                border-gray-300 rounded-md"
                        >
                            {/* Only show handles when expanded */}
                            {isExpanded && (
                                <BaseHandle
                                    type="source"
                                    position={Position.Right}
                                    id={`${index}`}
                                    style={{ ...defaultHandleStyle }}
                                />
                            )}
                            <div
                                className="flex-grow nodrag"
                                onMouseDown={(e) => e.stopPropagation()}
                            >
                                <Input
                                    type="text"
                                    value={choice}
                                    onChange={(e) => {
                                        const newChoices = [...data.metadata.choices];
                                        newChoices[index] = e.target.value;
                                        setBranchChoices(newChoices);
                                    }}
                                />
                            </div>
                            <Button
                                variant="ghost"
                                className="size-6 p-1"
                                onClick={() => removeChoice(index)}
                            >
                                <SquareX className="stroke-red-700" />
                            </Button>
                        </div>
                    ))}
                    <div className="flex justify-center">
                        <Button variant="ghost" className="p-1 text-blue-500" onClick={addChoice}>
                            Add output
                        </Button>
                    </div>
                </div>
            </StandardWorkflowNode>
            {/* Render collapsed handles outside WorkflowNode to avoid conflicts */}
            {!isExpanded &&
                data.metadata.choices.map((choice, index) => (
                    <BaseHandle
                        key={`collapsed-${index}`}
                        type="source"
                        position={Position.Right}
                        id={`${index}`}
                        style={{
                            ...defaultHandleStyle,
                            top: "50%",
                            right: -20,
                            position: "absolute",
                            transform: `translateY(${-20 + index * 12}px)`,
                        }}
                    />
                ))}
        </>
    );
}
