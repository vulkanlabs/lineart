"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import type { PolicyVersion, Component } from "@vulkanlabs/client-open";

import {
    WorkflowFrame,
    WorkflowApiProvider,
    WorkflowDataProvider,
    createWorkflowApiClient,
} from "@vulkanlabs/base/workflow";

/**
 * Props for the application workflow frame
 */
export type AppWorkflowFrameProps = {
    policyVersion: PolicyVersion;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
};

/**
 * Props for the unified workflow frame
 */
export type UnifiedWorkflowFrameProps = {
    workflowData: PolicyVersion | Component;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
};

// Add missing type for backward compatibility
export type ComponentWorkflowFrameProps = {
    component: Component;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
};

/**
 * Application-specific workflow frame that wraps the base WorkflowFrame
 * with app-specific API client and routing
 */
export function UnifiedWorkflowFrame({
    workflowData,
    onNodeClick = () => {},
    onPaneClick = () => {},
}: UnifiedWorkflowFrameProps) {
    const router = useRouter();
    const apiClient = createWorkflowApiClient();
    const handleRefresh = () => router.refresh();
    const handleToast = (message: string, options?: any) => toast(message, options);
    // Add empty config if required by WorkflowApiProvider
    return (
        <WorkflowApiProvider client={apiClient} config={{}}>
            <WorkflowDataProvider autoFetch={true} includeArchived={false}>
                <WorkflowFrame
                    policyVersion={workflowData}
                    onNodeClick={onNodeClick}
                    onPaneClick={onPaneClick}
                    toast={handleToast}
                    onRefresh={handleRefresh}
                />
            </WorkflowDataProvider>
        </WorkflowApiProvider>
    );
}
