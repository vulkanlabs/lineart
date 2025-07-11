"use client";

import React, { useCallback } from "react";
import { SquareX } from "lucide-react";
import { useShallow } from "zustand/react/shallow";
import { Position, type NodeChange } from "@xyflow/react";
import Editor from "@monaco-editor/react";

import { Input, Button } from "@vulkanlabs/base/ui";
import { BaseHandle } from "@vulkanlabs/base/ui";

import { useWorkflowStore } from "@/workflow/store";
import { StandardWorkflowNode, defaultHandleStyle } from "./base";
import type { VulkanNodeProps, VulkanNode } from "@/workflow/types/workflow";

/**
 * Branch node component - creates parallel execution paths
 */
export function BranchNode({ id, data, selected, height, width }: VulkanNodeProps) {
    const { updateNodeData, updateTargetDeps, onNodesChange } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            updateTargetDeps: state.updateTargetDeps,
            onNodesChange: state.onNodesChange,
        })),
    );

    const setSourceCode = useCallback(
        (code: string) => {
            const nodeData = data as VulkanNode["data"];
            const metadata = { ...nodeData.metadata, source_code: code };
            updateNodeData(id, { ...nodeData, metadata });
        },
        [id, data, updateNodeData],
    );

    const setBranchChoices = useCallback(
        (choices: string[]) => {
            const nodeData = data as VulkanNode["data"];
            const metadata = { ...nodeData.metadata, choices: choices };
            updateNodeData(id, { ...nodeData, metadata });
            updateTargetDeps?.(id);
        },
        [id, data, updateNodeData, updateTargetDeps],
    );

    const heightStepSize = 80; // Adjust this value as needed

    const addChoice = useCallback(() => {
        const newHeight = (height || 200) + heightStepSize;
        const nodeData = data as VulkanNode["data"];
        const choices = (nodeData.metadata?.choices as string[]) || [];
        const newChoices = [...choices, ""]; // TODO: do we need a default choice?
        const metadata = { ...nodeData.metadata, choices: newChoices };

        updateNodeData(id, { ...nodeData, metadata, minHeight: newHeight });

        onNodesChange?.([
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
            const newHeight = (height || 200) - heightStepSize;
            const nodeData = data as VulkanNode["data"];
            const choices = (nodeData.metadata?.choices as string[]) || [];
            const newChoices = [...choices];
            newChoices.splice(index, 1);

            const metadata = { ...nodeData.metadata, choices: newChoices };

            updateNodeData(id, { ...nodeData, metadata, minHeight: newHeight });

            // TODO: remove the edge whose source was deleted

            onNodesChange?.([
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

    const nodeData = data as VulkanNode["data"];
    const isExpanded = nodeData.detailsExpanded ?? true;
    const choices = (nodeData.metadata?.choices as string[]) || [];

    return (
        <>
            <StandardWorkflowNode
                id={id}
                selected={selected}
                data={nodeData}
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
                            value={nodeData.metadata?.source_code || ""}
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
                    {choices.map((choice, index) => (
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
                                        const newChoices = [...choices];
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
                choices.map((_, index) => (
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
