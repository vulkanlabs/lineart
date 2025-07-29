"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { Input, Textarea } from "@vulkanlabs/base/ui";

import { useWorkflowStore } from "@/workflow/store";
import { TerminateWorkflowNode } from "./base";
import type { VulkanNodeProps } from "@/workflow/types/workflow";
import type { TerminateNodeMetadata } from "@/workflow/types/nodes";

/**
 * Terminate node component - ends workflow execution
 */
export function TerminateNode({ id, data, selected, width }: VulkanNodeProps) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const [metadata, setMetadata] = useState<string>("");
    const [updateError, setUpdateError] = useState<string>("");

    // Initialize local state from node data
    useEffect(() => {
        // Cast metadata to the specific type for better type checking
        const nodeMetadata = data.metadata as TerminateNodeMetadata | undefined;
        const storedMetadata = nodeMetadata?.return_metadata;

        if (typeof storedMetadata === "string") {
            setMetadata(storedMetadata);
        } else if (storedMetadata && typeof storedMetadata === "object") {
            setMetadata(JSON.stringify(storedMetadata, null, 2));
        } else {
            setMetadata("");
        }

        setUpdateError("");
    }, [id, data]);

    const setReturnStatus = useCallback(
        (status: string) => {
            updateNodeData(id, {
                ...data,
                metadata: { ...data.metadata, return_status: status },
            });
        },
        [id, data, updateNodeData],
    );

    // Function to save the metadata
    const saveMetadata = useCallback(
        async (metadataString: string) => {
            setUpdateError("");

            try {
                updateNodeData(id, {
                    ...data,
                    metadata: { ...data.metadata, return_metadata: metadataString },
                });
            } catch (error) {
                setUpdateError(
                    `Failed to save: ${error instanceof Error ? error.message : "Unknown error"}`,
                );
            }
        },
        [id, data, updateNodeData],
    );

    const returnStatus = (data.metadata as any)?.return_status || "";

    return (
        <TerminateWorkflowNode id={id} selected={selected} data={data} width={width}>
            <div className="flex flex-col p-4 w-full h-fit">
                <div className="flex flex-col gap-4 h-full">
                    {/* Return Status Section */}
                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-gray-700">Return Status</label>
                        <div className="nodrag" onMouseDown={(e) => e.stopPropagation()}>
                            <Input
                                type="text"
                                value={returnStatus}
                                onChange={(e) => setReturnStatus(e.target.value)}
                                placeholder="e.g., success, failed, timeout"
                                className="text-sm"
                            />
                        </div>
                    </div>

                    {/* Return Metadata Section */}
                    <div className="flex flex-col gap-3 flex-grow min-h-0">
                        <label className="text-sm font-medium text-gray-700">Return Metadata</label>
                        <div className="nodrag flex flex-col gap-3 h-full overflow-y-auto">
                            <Textarea
                                value={metadata}
                                onChange={(e) => {
                                    setMetadata(e.target.value);
                                    setUpdateError("");
                                }}
                                onBlur={() => {
                                    saveMetadata(metadata);
                                }}
                                placeholder="[Optional metadata or template variables]"
                                rows={8}
                                className="w-full font-mono text-sm resize-vertical min-h-[120px] placeholder:text-gray-400 placeholder:italic focus:ring-blue-200"
                                onMouseDown={(e) => e.stopPropagation()}
                            />
                            {/* Error Messages */}
                            {updateError && (
                                <div className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-md border border-red-200 flex items-start gap-2">
                                    <div className="text-red-500 mt-0.5">✕</div>
                                    <div>
                                        <div className="font-medium">Save Failed</div>
                                        <div className="text-red-500">{updateError}</div>
                                    </div>
                                </div>
                            )}

                            {/* Helper Text */}
                            <div className="text-xs text-gray-600 bg-gray-50 px-3 py-2 rounded-md border">
                                <div className="font-medium text-gray-700 mb-1">
                                    Template Syntax:
                                </div>
                                <div className="space-y-1">
                                    <div>
                                        • Use{" "}
                                        <code className="bg-gray-200 px-1 rounded text-xs">
                                            {"{{nodeId.data}}"}
                                        </code>{" "}
                                        to reference node output
                                    </div>
                                    <div>• Mix with static text, JSON, or any format you need</div>
                                    <div>
                                        • Supports nested paths like{" "}
                                        <code className="bg-gray-200 px-1 rounded text-xs">
                                            {"{{node.data.field.subfield}}"}
                                        </code>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </TerminateWorkflowNode>
    );
}
