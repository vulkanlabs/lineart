"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import "@xyflow/react/dist/style.css";

import {
    WorkflowFrame,
    WorkflowApiProvider,
    WorkflowDataProvider,
    createWorkflowApiClient,
} from "@vulkanlabs/base/workflow";
import type { Workflow } from "@vulkanlabs/base/workflow";

/**
 * Props for the workflow frame
 */
export type AppWorkflowFrameProps = {
    workflowData: Workflow;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
};

/**
 * Application-specific workflow frame that wraps the base WorkflowFrame
 * with app-specific API client and routing
 */
export function AppWorkflowFrame({
    workflowData,
    onNodeClick = () => {},
    onPaneClick = () => {},
}: AppWorkflowFrameProps) {
    const router = useRouter();
    const apiClient = createWorkflowApiClient();
    const handleRefresh = () => router.refresh();
    const handleToast = (message: string, options?: any) => toast(message, options);
    // Add empty config if required by WorkflowApiProvider
    return (
        <WorkflowApiProvider client={apiClient} config={{}}>
            <WorkflowDataProvider autoFetch={true} includeArchived={false} projectId={undefined}>
                <WorkflowFrame
                    workflow={workflowData}
                    onNodeClick={onNodeClick}
                    onPaneClick={onPaneClick}
                    toast={handleToast}
                    onRefresh={handleRefresh}
                    projectId={undefined}
                />
            </WorkflowDataProvider>
        </WorkflowApiProvider>
    );
}
