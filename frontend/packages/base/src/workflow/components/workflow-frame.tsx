"use client";

import React from "react";
import type { Workflow } from "../api/types";

import { WorkflowProviderWrapper } from "./workflow/workflow-provider";
import { WorkflowCanvas } from "./workflow/workflow-canvas";
import { nodeTypes } from "./nodes";

/**
 * Props for the workflow frame component
 */
export type WorkflowFrameProps = {
    workflow: Workflow;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
    toast?: (message: string, options?: any) => void;
    onRefresh?: () => void;
    projectId?: string;
};

/**
 * Main workflow frame component that combines provider and canvas
 * This is the main entry point for embedding workflow functionality
 */
export function WorkflowFrame({
    workflow,
    onNodeClick = (e: React.MouseEvent, node: any) => {},
    onPaneClick = (e: React.MouseEvent) => {},
    toast,
    onRefresh,
    projectId,
}: WorkflowFrameProps) {
    return (
        <WorkflowProviderWrapper workflow={workflow}>
            <WorkflowCanvas
                workflow={workflow}
                nodeTypes={nodeTypes}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                toast={toast}
                onRefresh={onRefresh}
                projectId={projectId}
            />
        </WorkflowProviderWrapper>
    );
}
