"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useShallow } from "zustand/react/shallow";
import { Panel, PanelGroup } from "react-resizable-panels";

import { WorkflowProviderWrapper } from "./workflow/workflow-provider";
import { WorkflowCanvas } from "./workflow/workflow-canvas";
import { IntegratedWorkflowSidebar } from "./integrated-workflow-sidebar";
import { ResizeHandle } from "../../components/resize-handle";
import { useWorkflowStore } from "@/workflow/store/workflow-store";
import { nodeTypes } from "@/workflow/components/nodes";
import { useAutoSave } from "@/workflow/hooks/useAutoSave";
import { useWorkflowApi } from "@/workflow/api";
import type { Workflow } from "@/workflow/api/types";

/**
 * Custom hook for managing panel sizes with localStorage persistence and sidebar width integration
 */
function usePanelSizes() {
    const { sidebar, setSidebarWidth } = useWorkflowStore(
        useShallow((state) => ({
            sidebar: state.sidebar,
            setSidebarWidth: state.setSidebarWidth,
        })),
    );

    const [panelSizes, setPanelSizes] = useState<number[]>(() => {
        try {
            const saved = localStorage.getItem("workflow.panelSizes");
            const parsedSizes = saved ? JSON.parse(saved) : [70, 30];

            // If sidebar has a saved width, use it
            if (sidebar.width !== undefined) return [100 - sidebar.width, sidebar.width];

            return parsedSizes;
        } catch (e) {
            return [70, 30];
        }
    });

    const handlePanelResize = useCallback(
        (sizes: number[]) => {
            setPanelSizes(sizes);
            localStorage.setItem("workflow.panelSizes", JSON.stringify(sizes));

            // Update sidebar width in store when panels are resized
            if (sidebar.isOpen && sizes.length > 1) setSidebarWidth(sizes[1]);
        },
        [sidebar.isOpen, setSidebarWidth],
    );

    const resetPanelSizes = useCallback(() => {
        const defaultSizes = [70, 30];
        setPanelSizes(defaultSizes);
        localStorage.setItem("workflow.panelSizes", JSON.stringify(defaultSizes));
        setSidebarWidth(30); // Reset sidebar width to default
    }, [setSidebarWidth]);

    // Update panel sizes when sidebar width changes in store
    useEffect(() => {
        if (sidebar.width !== undefined && sidebar.isOpen) {
            const newSizes = [100 - sidebar.width, sidebar.width];
            setPanelSizes(newSizes);
            localStorage.setItem("workflow.panelSizes", JSON.stringify(newSizes));
        }
    }, [sidebar.width, sidebar.isOpen]);

    return { panelSizes, handlePanelResize, resetPanelSizes };
}
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
            <WorkflowFrameInner
                workflow={workflow}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                toast={toast}
                onRefresh={onRefresh}
                projectId={projectId}
            />
        </WorkflowProviderWrapper>
    );
}

/**
 * Inner workflow frame component that has access to the store
 * This component is wrapped by the WorkflowProvider
 */
function WorkflowFrameInner({
    workflow,
    onNodeClick,
    onPaneClick,
    toast,
    onRefresh,
    projectId,
}: WorkflowFrameProps) {
    return (
        <>
            <AutoSaveStatusIntegration workflow={workflow} projectId={projectId} />
            <div className="w-full h-full bg-gray-50">
                <div className="w-full h-full bg-white">
                    <WorkflowCanvas
                        workflow={workflow}
                        nodeTypes={nodeTypes}
                        onNodeClick={onNodeClick}
                        onPaneClick={onPaneClick}
                        toast={toast}
                        onRefresh={onRefresh}
                    />
                </div>
            </div>
        </>
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
    console.log(
        "Rendering AutoSaveStatusIntegration for workflow",
        workflow.workflow?.workflow_id,
        projectId,
    );
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

        const handleClearSaveError = () => {
            const clearEvent = new CustomEvent("workflow:clear-save-error");
            window.dispatchEvent(clearEvent);
        };

        window.addEventListener("workflow:toggle-autosave", handleToggle as EventListener);
        window.addEventListener("workflow:clear-save-error", handleClearSaveError);

        return () => {
            window.removeEventListener("workflow:toggle-autosave", handleToggle as EventListener);
            window.removeEventListener("workflow:clear-save-error", handleClearSaveError);
        };
    }, [autoSave.autoSaveEnabled, toggleAutoSave]);

    return null;
}
