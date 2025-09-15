"use client";

import React, { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";
import { Code2 } from "lucide-react";

import { StandardWorkflowNode } from "./base";
import { NodeHeaderAction } from "@vulkanlabs/base/ui";
import { useWorkflowStore } from "@/workflow/store";
import type { VulkanNodeProps } from "@/workflow/types/workflow";

// Default Python template for transform nodes
const DEFAULT_PYTHON_TEMPLATE = `def transform(data):
    # Your transformation logic here
    return data`;

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
    const isCurrentlyEditing = sidebar.isOpen && sidebar.selectedNodeId === id;

    // Show default template if no code, otherwise show actual code
    const displayCode = sourceCode.trim() || DEFAULT_PYTHON_TEMPLATE;

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
            className="bg-gray-50 border border-gray-200 rounded p-3 cursor-pointer hover:bg-gray-100 transition-colors h-full"
            onClick={handleEditCode}
        >
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed h-full overflow-auto">
                {displayCode}
            </pre>
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
            <div className="px-4 pt-2 pb-4 flex flex-col h-full">
                <div className="flex-1 min-h-0">{renderCodePreview()}</div>
            </div>
        </StandardWorkflowNode>
    );
}
