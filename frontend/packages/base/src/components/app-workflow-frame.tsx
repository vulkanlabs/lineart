"use client";

import React, { useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { createGlobalToast } from "./toast";
import { z } from "zod";

import {
    WorkflowFrame,
    WorkflowApiProvider,
    WorkflowDataProvider,
    createWorkflowApiClient,
    type Workflow,
} from "../workflow";

export type AppWorkflowFrameProps = {
    workflowData: Workflow;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
    projectId?: string;
};

/**
 * Configurable application workflow frame that adapts to different deployment modes.
 *
 * Performance optimized with React.memo to prevent unnecessary re-renders when props haven't changed.
 * Uses custom comparison function to handle union types and optional props correctly.
 *
 * @param props - Union type supporting both global and project scope configurations
 * @returns Memoized React component with workflow frame functionality
 */
export const AppWorkflowFrame = React.memo<AppWorkflowFrameProps>(
    function AppWorkflowFrame(props: AppWorkflowFrameProps) {
        const { workflowData, onNodeClick = () => {}, onPaneClick = () => {} } = props;

        const router = useRouter();

        // Memoize API client creation (expensive operation)
        const apiClient = useMemo(() => createWorkflowApiClient(), []);

        // Memoize event handlers to prevent child re-renders
        const handleRefresh = useCallback(() => router.refresh(), [router]);
        const toast = createGlobalToast();
        const handleToast = useCallback(
            (message: string, options?: any) => toast(message, options),
            [],
        );

        // Extract projectId and policyId based on props type
        const projectId = "projectId" in props ? props.projectId : undefined;

        return (
            <WorkflowApiProvider client={apiClient} config={{}}>
                <WorkflowDataProvider
                    autoFetch={true}
                    includeArchived={false}
                    projectId={projectId}
                >
                    <WorkflowFrame
                        workflow={workflowData}
                        onNodeClick={onNodeClick}
                        onPaneClick={onPaneClick}
                        toast={handleToast}
                        onRefresh={handleRefresh}
                        projectId={projectId ? projectId : undefined}
                    />
                </WorkflowDataProvider>
            </WorkflowApiProvider>
        );
    },
    (prevProps, nextProps) => {
        // Custom comparison for performance optimization
        return (
            prevProps.workflowData === nextProps.workflowData &&
            prevProps.onNodeClick === nextProps.onNodeClick &&
            prevProps.onPaneClick === nextProps.onPaneClick &&
            ("projectId" in prevProps ? prevProps.projectId : undefined) ===
                ("projectId" in nextProps ? nextProps.projectId : undefined)
        );
    },
);
