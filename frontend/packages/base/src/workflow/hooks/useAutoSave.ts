import { useEffect, useRef, useCallback } from "react";
import { useShallow } from "zustand/react/shallow";
import { useWorkflowStore } from "../store/workflow-store";
import type { WorkflowApiClient } from "../api/types";

interface UseAutoSaveConfig {
    apiClient: WorkflowApiClient;
    workflow: any;
    getUIMetadata?: () => { [key: string]: any };
    projectId?: string;
}

export function useAutoSave({
    apiClient,
    workflow,
    getUIMetadata = () => ({}),
    projectId,
}: UseAutoSaveConfig) {
    const timerRef = useRef<NodeJS.Timeout | null>(null);
    const isInitialMount = useRef(true);

    const { autoSave, markSaving, markSaved, markSaveError, getSpec } = useWorkflowStore(
        useShallow((state) => ({
            autoSave: state.autoSave,
            markSaving: state.markSaving,
            markSaved: state.markSaved,
            markSaveError: state.markSaveError,
            getSpec: state.getSpec,
        })),
    );

    // Stable save function that doesn't change on every render
    const executeAutoSave = useCallback(async (): Promise<void> => {
        try {
            markSaving();

            const spec = getSpec();
            const uiMetadata = getUIMetadata();

            await apiClient.saveWorkflowSpec(workflow, spec, uiMetadata, projectId);

            markSaved();
        } catch (error) {
            const currentError = error instanceof Error ? error : new Error("Auto-save failed");
            markSaveError(currentError.message);
        }
    }, [
        apiClient,
        workflow,
        projectId,
        markSaving,
        markSaved,
        markSaveError,
        getSpec,
        getUIMetadata,
    ]);

    // Clear any existing timer
    const clearTimer = useCallback(() => {
        if (timerRef.current !== null) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
            return true;
        }
        return false;
    }, []);

    // Schedule a new auto-save
    const scheduleAutoSave = useCallback(() => {
        timerRef.current = setTimeout(() => {
            executeAutoSave();
            timerRef.current = null;
        }, autoSave.autoSaveInterval);
    }, [autoSave.autoSaveInterval, executeAutoSave]);

    // Main effect that handles auto-save logic
    useEffect(() => {
        // Skip auto-save on initial mount
        if (isInitialMount.current) {
            isInitialMount.current = false;
            return;
        }

        clearTimer();

        // Schedule new timer if conditions are met
        if (autoSave.hasUnsavedChanges && autoSave.autoSaveEnabled && !autoSave.isSaving)
            scheduleAutoSave();
    }, [
        autoSave.hasUnsavedChanges,
        autoSave.autoSaveEnabled,
        autoSave.isSaving,
        clearTimer,
        scheduleAutoSave,
    ]);

    // Cleanup timer on unmount
    useEffect(() => {
        return () => {
            if (timerRef.current) {
                clearTimeout(timerRef.current);
                timerRef.current = null;
            }
        };
    }, []);

    return {
        isAutoSaving: autoSave.isSaving,
        hasUnsavedChanges: autoSave.hasUnsavedChanges,
        lastSaved: autoSave.lastSaved,
        saveError: autoSave.saveError,
        autoSaveEnabled: autoSave.autoSaveEnabled,
        performManualSave: executeAutoSave, // For manual save button
    };
}
