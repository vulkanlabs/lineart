"use client";

import React, { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";
import { Code2 } from "lucide-react";

import { StandardWorkflowNode } from "./base";
import { NodeHeaderAction } from "@vulkanlabs/base/ui";
import { useWorkflowStore } from "@/workflow/store";
import type { VulkanNodeProps } from "@/workflow/types/workflow";

/**
 * Transform node component - processes and transforms data using integrated sidebar
 */
export function TransformNode({ id, data, selected, height, width }: VulkanNodeProps) {
    const { openSidebar, sidebar } = useWorkflowStore(
        useShallow((state) => ({
            openSidebar: state.openSidebar,
            sidebar: state.sidebar,
        })),
    );

    const sourceCode = data.metadata?.source_code || "";
    const hasCode = sourceCode.trim().length > 0;
    const isCurrentlyEditing = sidebar.isOpen && sidebar.selectedNodeId === id;

    const handleEditCode = useCallback(() => {
        openSidebar(id, "code-editor");
    }, [id, openSidebar]);

    const customHeaderActions = (
        <NodeHeaderAction onClick={handleEditCode} label="Edit code">
            <Code2 className="stroke-slate-600" size={16} />
        </NodeHeaderAction>
    );

    const renderCodePreview = () => (
        <div
            className="max-h-40 overflow-y-auto bg-gray-50 border border-gray-200 rounded p-3 cursor-pointer hover:bg-gray-100 transition-colors"
            onClick={handleEditCode}
        >
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
                {sourceCode}
            </pre>
        </div>
    );

    const renderEmptyState = () => (
        <div
            className="flex flex-col items-center justify-center text-gray-500 py-8 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 hover:border-gray-400 transition-all duration-200"
            onClick={handleEditCode}
        >
            <Code2 className="w-8 h-8 mb-3 text-gray-400" />
            <span className="text-sm font-medium text-gray-600 mb-1">Click to add code</span>
            <span className="text-xs text-gray-400">Write your transformation logic</span>
        </div>
    );

    return (
        <StandardWorkflowNode
            id={id}
            selected={selected || isCurrentlyEditing}
            data={data}
            height={height}
            width={width}
            customHeaderActions={customHeaderActions}
        >
            <div className="px-4 pt-2 pb-4">
                {hasCode ? renderCodePreview() : renderEmptyState()}
            </div>
        </StandardWorkflowNode>
    );
}
