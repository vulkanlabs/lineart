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
 * Custom hook for managing panel sizes with localStorage persistence
 */
function usePanelSizes() {
    const [panelSizes, setPanelSizes] = useState<number[]>(() => {
        try {
            const saved = localStorage.getItem("workflow.panelSizes");
            return saved ? JSON.parse(saved) : [70, 30];
        } catch (e) {
            return [70, 30];
        }
    });

    const handlePanelResize = useCallback((sizes: number[]) => {
        setPanelSizes(sizes);
        localStorage.setItem("workflow.panelSizes", JSON.stringify(sizes));
    }, []);

    const resetPanelSizes = useCallback(() => {
        const defaultSizes = [70, 30];
        setPanelSizes(defaultSizes);
        localStorage.setItem("workflow.panelSizes", JSON.stringify(defaultSizes));
    }, []);

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
    const { sidebar } = useWorkflowStore(
        useShallow((state) => ({
            sidebar: state.sidebar,
        })),
    );

    const { panelSizes, handlePanelResize, resetPanelSizes } = usePanelSizes();

    return (
        <>
            <AutoSaveStatusIntegration workflow={workflow} projectId={projectId} />
            <div className="w-full h-full bg-gray-50">
                <PanelGroup
                    direction="horizontal"
                    onLayout={handlePanelResize}
                    className="h-full w-full"
                >
                    <Panel
                        defaultSize={panelSizes[0]}
                        minSize={40}
                        key={sidebar.isOpen ? "with-sidebar" : "without-sidebar"}
                    >
                        <div className="w-full h-full bg-white">
                            <WorkflowCanvas
                                workflow={workflow}
                                nodeTypes={nodeTypes}
                                onNodeClick={onNodeClick}
                                onPaneClick={onPaneClick}
                                toast={toast}
                                onRefresh={onRefresh}
                                projectId={projectId}
                            />
                        </div>
                    </Panel>

                    {sidebar.isOpen && (
                        <>
                            <ResizeHandle direction="horizontal" onDoubleClick={resetPanelSizes} />
                            <Panel
                                defaultSize={panelSizes[1]}
                                minSize={20}
                                maxSize={60}
                                key="sidebar-panel" // Stable key for sidebar panel
                            >
                                <IntegratedWorkflowSidebar />
                            </Panel>
                        </>
                    )}
                </PanelGroup>
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
