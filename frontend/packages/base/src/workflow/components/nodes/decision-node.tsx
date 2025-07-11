"use client";

import React, { useCallback, useState } from "react";
import { SquareX } from "lucide-react";
import { useShallow } from "zustand/react/shallow";
import { Position, type NodeChange } from "@xyflow/react";

import { Input, Button, Label } from "@vulkanlabs/base/ui";
import { BaseHandle } from "@vulkanlabs/base/ui";

import { useWorkflowStore } from "@/workflow/store";
import { StandardWorkflowNode, defaultHandleStyle } from "./base";
import type { VulkanNodeProps, VulkanNode } from "@/workflow/types/workflow";

interface DecisionCondition {
    decision_type: "if" | "else-if" | "else";
    condition?: string; // Jinja2 template string for 'if' and 'else-if'
    output: string;
}

interface DecisionMetadata {
    conditions: DecisionCondition[];
}

/**
 * Decision node component - makes conditional decisions in workflow
 */
export function DecisionNode({ id, data, selected, height, width }: VulkanNodeProps) {
    const { updateNodeData, updateTargetDeps, onNodesChange, edges, removeEdge } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            updateTargetDeps: state.updateTargetDeps,
            onNodesChange: state.onNodesChange,
            edges: state.edges,
            removeEdge: state.removeEdge,
        })),
    );

    const initialConditions: DecisionCondition[] = data.metadata?.conditions || [
        { decision_type: "if", condition: "", output: "condition_1" },
        { decision_type: "else", output: "condition_2" },
    ];

    const [conditions, setConditions] = useState<DecisionCondition[]>(initialConditions);

    const updateConditions = useCallback(
        (newConditions: DecisionCondition[]) => {
            setConditions(newConditions);
            const metadata: DecisionMetadata = { conditions: newConditions };
            updateNodeData(id, { ...data, metadata });
            updateTargetDeps?.(id);

            // More accurate height calculation:
            // Base: 120px (padding + button)
            // Per condition: 94px (label + input + padding + border + spacing)
            const newHeight = 120 + newConditions.length * 94;
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
        [id, data, updateNodeData, updateTargetDeps, onNodesChange, width],
    );

    const addElseIf = useCallback(() => {
        const newConditions = [...conditions];
        // Insert new else-if before the final else condition
        const elseIndex = newConditions.findIndex((c) => c.decision_type === "else");
        if (elseIndex !== -1) {
            newConditions.splice(elseIndex, 0, {
                decision_type: "else-if",
                condition: "",
                output: `condition_${newConditions.length}`,
            });
            updateConditions(newConditions);
        }
    }, [conditions, updateConditions]);

    const removeCondition = useCallback(
        (index: number) => {
            // Prevent removing if or else conditions
            if (
                conditions[index].decision_type === "if" ||
                conditions[index].decision_type === "else"
            ) {
                return;
            }
            const newConditions = [...conditions];
            newConditions.splice(index, 1);
            updateConditions(newConditions);

            // Remove edges connected to the removed output handle
            edges.forEach((edge) => {
                if (edge.source === id && edge.sourceHandle === `${index}`) {
                    removeEdge?.(edge.id);
                }
            });
        },
        [conditions, updateConditions, edges, removeEdge, id],
    );

    const updateCondition = useCallback(
        (index: number, updates: Partial<DecisionCondition>) => {
            const newConditions = [...conditions];
            newConditions[index] = {
                ...newConditions[index],
                ...updates,
            };
            updateConditions(newConditions);
        },
        [conditions, updateConditions],
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
                <div className="h-full flex flex-col gap-3 p-3">
                    {conditions.map((condition, index) => (
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
                            <div className="flex-grow flex flex-col gap-2 nodrag">
                                <Label className="font-medium">
                                    {condition.decision_type === "if"
                                        ? "if"
                                        : condition.decision_type === "else-if"
                                          ? "else if"
                                          : "else"}
                                </Label>
                                {condition.decision_type !== "else" && (
                                    <Input
                                        type="text"
                                        value={condition.condition || ""}
                                        onChange={(e) =>
                                            updateCondition(index, { condition: e.target.value })
                                        }
                                        placeholder="input_node.score >= 750"
                                        onMouseDown={(e) => e.stopPropagation()}
                                    />
                                )}
                            </div>
                            {condition.decision_type === "else-if" && (
                                <Button
                                    variant="ghost"
                                    className="size-6 p-1"
                                    onClick={() => removeCondition(index)}
                                >
                                    <SquareX className="stroke-red-700" />
                                </Button>
                            )}
                        </div>
                    ))}
                    <div className="flex justify-center">
                        <Button variant="ghost" className="p-1 text-blue-500" onClick={addElseIf}>
                            Add Condition
                        </Button>
                    </div>
                </div>
            </StandardWorkflowNode>
            {/* Render collapsed handles outside WorkflowNode to avoid conflicts */}
            {!isExpanded &&
                conditions.map((condition, index) => (
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
                            transform: `translateY(${-20 + index * 12}px)`, // Adjust vertical spacing
                        }}
                    />
                ))}
        </>
    );
}
