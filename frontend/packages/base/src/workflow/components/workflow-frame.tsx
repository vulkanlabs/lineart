"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useShallow } from "zustand/react/shallow";

import { WorkflowProviderWrapper } from "./workflow/workflow-provider";
import { WorkflowCanvas } from "./workflow/workflow-canvas";
import { useWorkflowStore } from "@/workflow/store/workflow-store";
import { nodeTypes } from "@/workflow/components/nodes";
import { useAutoSave } from "@/workflow/hooks/useAutoSave";
import { useWorkflowApi } from "@/workflow/api";
import type { Workflow } from "@/workflow/api/types";

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
            <AutoSaveStatusIntegration workflow={workflow} projectId={projectId} />
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

type AutoSaveStatusIntegrationProps = {
    workflow: Workflow;
    projectId?: string;
};

/**
 * Integrated auto-save status component
 * Handles communication between workflow state and navigation bar
 */
function AutoSaveStatusIntegration({ workflow, projectId }: AutoSaveStatusIntegrationProps) {
    const { nodes, autoSave, toggleAutoSave } = useWorkflowStore(
        useShallow((state) => ({
            nodes: state.nodes,
            autoSave: state.autoSave,
            toggleAutoSave: state.toggleAutoSave,
        })),
    );

    const [isInitialized, setIsInitialized] = useState(false);

    useEffect(() => {
        setIsInitialized(true);
    }, []);

    // Auto-save integration - use stable reference to current nodes
    const api = useWorkflowApi();

    const getUIMetadata = useCallback(() => {
        return Object.fromEntries(
            nodes.map((node) => [
                node.data.name,
                { position: node.position, width: node.width, height: node.height },
            ]),
        );
    }, [nodes]);

    const { isAutoSaving, hasUnsavedChanges, lastSaved, saveError, autoSaveEnabled } = useAutoSave({
        apiClient: api,
        workflow,
        getUIMetadata,
        projectId,
    });

    // Sync workflow auto-save state to navigation bar
    useEffect(() => {
        if (!isInitialized) return;

        const event = new CustomEvent("workflow:autosave-status", {
            detail: {
                hasUnsavedChanges: autoSave.hasUnsavedChanges,
                autoSaveEnabled: autoSave.autoSaveEnabled,
                isSaving: autoSave.isSaving,
                lastSaved: autoSave.lastSaved,
                saveError: autoSave.saveError,
                retryCount: autoSave.retryCount,
                autoSaveInterval: autoSave.autoSaveInterval,
            },
        });
        window.dispatchEvent(event);
    }, [autoSave, isInitialized]);

    // Handle commands from navigation bar
    useEffect(() => {
        const handleToggle = (event: CustomEvent) => {
            if (event.detail.enabled !== autoSave.autoSaveEnabled) toggleAutoSave();
        };

        const handleManualSave = () => {
            const saveEvent = new CustomEvent("workflow:manual-save");
            window.dispatchEvent(saveEvent);
        };

        window.addEventListener("navigation:toggle-autosave", handleToggle as EventListener);
        window.addEventListener("navigation:manual-save", handleManualSave);

        return () => {
            window.removeEventListener("navigation:toggle-autosave", handleToggle as EventListener);
            window.removeEventListener("navigation:manual-save", handleManualSave);
        };
    }, [autoSave.autoSaveEnabled, toggleAutoSave]);

    return null;
}
