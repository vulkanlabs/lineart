"use client";

import React, { useMemo, type ReactNode } from "react";
import { ReactFlowProvider } from "@xyflow/react";

import { WorkflowStoreProvider as StoreProvider } from "@/workflow/store";
import { useWorkflowApi, Workflow } from "@/workflow/api";
import { createWorkflowState } from "@/workflow/utils/workflow-state";
import type { WorkflowState } from "@/workflow/types/workflow";

/**
 * Props for the workflow provider wrapper
 */
export type WorkflowProviderWrapperProps = {
    children: ReactNode;
    workflow: Workflow;
};

/**
 * Provider wrapper that combines ReactFlow provider with workflow store provider
 * and initializes the workflow state from the policy version
 */
export function WorkflowProviderWrapper({ children, workflow }: WorkflowProviderWrapperProps) {
    const apiClient = useWorkflowApi();

    /**
     * Create initial workflow state from workflow data
     */
    const initialState: WorkflowState = useMemo(() => {
        return createWorkflowState(workflow);
    }, [workflow]);
    console.log("WorkflowProviderWrapper: initialState", initialState);

    return (
        <ReactFlowProvider>
            <StoreProvider initialState={initialState} apiClient={apiClient}>
                {children}
            </StoreProvider>
        </ReactFlowProvider>
    );
}
