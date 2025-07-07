"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import type { PolicyVersion } from "@vulkan/client-open";

import {
    WorkflowFrame,
    WorkflowApiProvider,
    WorkflowDataProvider,
    createWorkflowApiClient,
} from "@vulkan/base/workflow";

/**
 * Props for the application workflow frame
 */
export type AppWorkflowFrameProps = {
    policyVersion: PolicyVersion;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
};

/**
 * Application-specific workflow frame that wraps the base WorkflowFrame
 * with app-specific API client and routing
 */
export function AppWorkflowFrame({
    policyVersion,
    onNodeClick = () => {},
    onPaneClick = () => {},
}: AppWorkflowFrameProps) {
    const router = useRouter();

    // Create API client that uses our app's API routes
    const apiClient = createWorkflowApiClient();

    // Handle refresh by refreshing the router
    const handleRefresh = () => {
        router.refresh();
    };

    // App-specific toast function
    const handleToast = (message: string, options?: any) => {
        toast(message, options);
    };

    return (
        <WorkflowApiProvider client={apiClient}>
            <WorkflowDataProvider autoFetch={true} includeArchived={false}>
                <WorkflowFrame
                    policyVersion={policyVersion}
                    onNodeClick={onNodeClick}
                    onPaneClick={onPaneClick}
                    toast={handleToast}
                    onRefresh={handleRefresh}
                />
            </WorkflowDataProvider>
        </WorkflowApiProvider>
    );
}
