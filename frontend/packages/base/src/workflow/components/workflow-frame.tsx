"use client";

import React from "react";
import type { PolicyVersion } from "@vulkanlabs/client-open";

import { WorkflowProviderWrapper } from "./workflow/workflow-provider";
import { WorkflowCanvas } from "./workflow/workflow-canvas";
import { nodeTypes } from "./nodes";

/**
 * Props for the workflow frame component
 */
export type WorkflowFrameProps = {
    policyVersion: PolicyVersion;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
    toast?: (message: string, options?: any) => void;
    onRefresh?: () => void;
};

/**
 * Main workflow frame component that combines provider and canvas
 * This is the main entry point for embedding workflow functionality
 */
export function WorkflowFrame({
    policyVersion,
    onNodeClick = (e: React.MouseEvent, node: any) => {},
    onPaneClick = (e: React.MouseEvent) => {},
    toast,
    onRefresh,
}: WorkflowFrameProps) {
    return (
        <WorkflowProviderWrapper policyVersion={policyVersion}>
            <WorkflowCanvas
                policyVersion={policyVersion}
                nodeTypes={nodeTypes}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                toast={toast}
                onRefresh={onRefresh}
            />
        </WorkflowProviderWrapper>
    );
}
