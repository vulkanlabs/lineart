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
    const activityTimerRef = useRef<NodeJS.Timeout | null>(null);
    const getUIMetadataRef = useRef(getUIMetadata);
    const autoSaveStateRef = useRef({
        hasUnsavedChanges: false,
        autoSaveEnabled: true,
        isSaving: false,
    });
    const isInitialMount = useRef(true);

    // Update the ref when getUIMetadata changes
    useEffect(() => {
        getUIMetadataRef.current = getUIMetadata;
    }, [getUIMetadata]);

    const { autoSave, markSaving, markSaved, markSaveError, getSpec } = useWorkflowStore(
        useShallow((state) => ({
            autoSave: state.autoSave,
            markSaving: state.markSaving,
            markSaved: state.markSaved,
            markSaveError: state.markSaveError,
            getSpec: state.getSpec,
        })),
    );

    // Update the ref whenever autoSave state changes
    useEffect(() => {
        autoSaveStateRef.current = autoSave;
    }, [autoSave]);

    // Create stable references to avoid dependency issues
    const performAutoSave = useCallback(async (): Promise<void> => {
        let spec, uiMetadata; // Declare variables for error logging

        try {
            markSaving();

            spec = getSpec();
            // Use the ref to get current UI metadata without dependency issues
            uiMetadata = getUIMetadataRef.current();

            await apiClient.saveWorkflowSpec(workflow, spec, uiMetadata, true, projectId); // isAutoSave = true

            markSaved();
        } catch (error) {
            const currentError = error instanceof Error ? error : new Error("Auto-save failed");
            markSaveError(currentError.message);
        }
    }, [apiClient, workflow, projectId, markSaving, markSaved, markSaveError, getSpec]); // Add projectId to deps

    // React to changes in workflow state - only depend on the specific values we need
    useEffect(() => {
        // Skip auto-save on initial mount to prevent immediate save after page load
        if (isInitialMount.current) {
            isInitialMount.current = false;
            return;
        }

        // Clear any existing timer
        if (activityTimerRef.current) {
            clearTimeout(activityTimerRef.current);
            activityTimerRef.current = null;
        }

        // Only schedule auto-save if we have unsaved changes, auto-save is enabled,
        // and we're not currently saving
        if (autoSave.hasUnsavedChanges && autoSave.autoSaveEnabled && !autoSave.isSaving) {
            activityTimerRef.current = setTimeout(() => {
                // Double-check that we still need to save before executing
                const currentState = autoSaveStateRef.current;
                if (
                    currentState.hasUnsavedChanges &&
                    currentState.autoSaveEnabled &&
                    !currentState.isSaving
                ) {
                    performAutoSave();
                }
            }, 10000); // Reduced delay for better UX
        }
    }, [autoSave.hasUnsavedChanges, autoSave.autoSaveEnabled, autoSave.isSaving, performAutoSave]);

    // Cleanup timer on unmount
    useEffect(() => {
        return () => {
            if (activityTimerRef.current) clearTimeout(activityTimerRef.current);
        };
    }, []);

    return {
        isAutoSaving: autoSave.isSaving,
        hasUnsavedChanges: autoSave.hasUnsavedChanges,
        lastSaved: autoSave.lastSaved,
        saveError: autoSave.saveError,
        autoSaveEnabled: autoSave.autoSaveEnabled,
        performManualSave: () => performAutoSave(), // For manual save button
    };
}
