import { useEffect, useRef, useCallback } from "react";
import { useShallow } from "zustand/react/shallow";
import { useWorkflowStore } from "../store/workflow-store";
import type { WorkflowApiClient } from "../api/types";
import { createGlobalToast } from "../../components/toast";

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
    const getUIMetadataRef = useRef(getUIMetadata);
    const isInitialMount = useRef(true);
    const toast = createGlobalToast();

    // Update the ref when getUIMetadata changes
    useEffect(() => {
        getUIMetadataRef.current = getUIMetadata;
    }, [getUIMetadata]);

    const { autoSave, markSaving, markSaved, markSaveError, clearSaveError, getSpec } =
        useWorkflowStore(
            useShallow((state) => ({
                autoSave: state.autoSave,
                markSaving: state.markSaving,
                markSaved: state.markSaved,
                markSaveError: state.markSaveError,
                clearSaveError: state.clearSaveError,
                getSpec: state.getSpec,
            })),
        );

    // Stable save function that doesn't change on every render
    const executeAutoSave = useCallback(
        async (isManual = false): Promise<void> => {
            try {
                markSaving();

                const spec = getSpec();
                const uiMetadata = getUIMetadataRef.current();

                const result = await apiClient.saveWorkflowSpec(
                    workflow,
                    spec,
                    uiMetadata,
                    projectId,
                );

                // Only mark as saved if the result indicates success
                if (result && result.success) {
                    markSaved();
                    // Show success toast only for manual saves, after marking as saved
                    if (isManual) {
                        toast("Workflow saved", {
                            description: "Workflow saved successfully.",
                            dismissible: true,
                        });
                    }
                } else {
                    // API client handles all error parsing, just use the error message
                    const errorMessage = result?.error || "Save failed";
                    markSaveError(errorMessage);
                    // Show error toast only for manual saves
                    if (isManual) {
                        toast.error("Failed to save workflow", {
                            description: errorMessage,
                            dismissible: true,
                        });
                    }
                }
            } catch (error) {
                const currentError = error instanceof Error ? error : new Error("Auto-save failed");
                markSaveError(currentError.message);
                // Show error toast only for manual saves
                if (isManual) {
                    toast.error("Failed to save workflow", {
                        description: currentError.message,
                        dismissible: true,
                    });
                }
            }
        },
        [apiClient, workflow, projectId, markSaving, markSaved, markSaveError, getSpec, toast],
    );

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

    // Handle manual save and clear error events
    useEffect(() => {
        const handleManualSave = () => {
            executeAutoSave(true); // Mark as manual save for toast notifications
        };

        const handleClearSaveError = () => {
            clearSaveError();
        };

        window.addEventListener("workflow:manual-save", handleManualSave);
        window.addEventListener("workflow:clear-save-error", handleClearSaveError);

        return () => {
            window.removeEventListener("workflow:manual-save", handleManualSave);
            window.removeEventListener("workflow:clear-save-error", handleClearSaveError);
        };
    }, [executeAutoSave, clearSaveError]);

    // Main effect that handles auto-save logic
    useEffect(() => {
        // Skip auto-save on initial mount
        if (isInitialMount.current) {
            isInitialMount.current = false;
            return;
        }

        clearTimer();

        // Schedule new timer if conditions are met (including no save error to prevent auto-retry)
        if (
            autoSave.hasUnsavedChanges &&
            autoSave.autoSaveEnabled &&
            !autoSave.isSaving &&
            !autoSave.saveError
        )
            scheduleAutoSave();
    }, [
        autoSave.hasUnsavedChanges,
        autoSave.autoSaveEnabled,
        autoSave.isSaving,
        autoSave.saveError,
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

    // Manual save function
    const performManualSave = useCallback(() => executeAutoSave(true), [executeAutoSave]);

    return {
        isAutoSaving: autoSave.isSaving,
        hasUnsavedChanges: autoSave.hasUnsavedChanges,
        lastSaved: autoSave.lastSaved,
        saveError: autoSave.saveError,
        autoSaveEnabled: autoSave.autoSaveEnabled,
        performManualSave,
    };
}
