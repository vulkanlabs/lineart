"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { Input, Textarea, Button } from "@vulkanlabs/base/ui";

import { useWorkflowStore } from "@/workflow/store";
import { TerminateWorkflowNode } from "./base";
import type { VulkanNodeProps } from "@/workflow/types/workflow";
import type { TerminateNodeMetadata } from "@/workflow/types/nodes";

/**
 * Template syntax help component - shows template usage examples
 */
function TemplateHelp() {
    return (
        <div className="bg-slate-50 border border-slate-200 rounded shadow-sm mt-2 p-3 w-full">
            <h4 className="text-sm font-semibold mb-2 text-slate-600">Template Syntax</h4>
            <div className="text-xs text-gray-600 space-y-1">
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
    );
}

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
    const [showTemplateHelp, setShowTemplateHelp] = useState<boolean>(false);

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

    const toggleTemplateHelp = useCallback(() => {
        setShowTemplateHelp((prev) => !prev);
    }, []);

    const returnStatus = (data.metadata as any)?.return_status || "";

    // Footer content with template syntax toggle button
    const footerContent = (
        <div className="flex gap-1 px-3 py-2 border-t border-slate-200 mt-1">
            <Button variant="outline" size="sm" onClick={toggleTemplateHelp}>
                {showTemplateHelp ? "Hide Template Syntax" : "Show Template Syntax"}
            </Button>
        </div>
    );

    return (
        <>
            <TerminateWorkflowNode
                id={id}
                selected={selected}
                data={data}
                width={width}
                footerContent={footerContent}
            >
                <div className="flex flex-col gap-3 p-3">
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

                    <hr className="border-slate-200" />

                    {/* Return Metadata Section */}
                    <div className="flex flex-col gap-2">
                        <label className="text-sm font-medium text-gray-700">Return Metadata</label>
                        <div className="nodrag flex flex-col gap-2">
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
                                rows={6}
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
                        </div>
                    </div>
                </div>
            </TerminateWorkflowNode>
            {showTemplateHelp && <TemplateHelp />}
        </>
    );
}
