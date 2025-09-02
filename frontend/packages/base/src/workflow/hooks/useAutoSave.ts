import { useEffect, useRef, useCallback } from "react";
import { useWorkflowStore } from "../store/workflow-store";
import type { WorkflowApiClient } from "../api/types";

interface UseAutoSaveConfig {
    apiClient: WorkflowApiClient;
    workflow: any;
    getUIMetadata?: () => { [key: string]: any };
    activityDelay?: number; // Default: 15000ms (15s)
    fallbackInterval?: number; // Default: 60000ms (60s)
}

export function useAutoSave({
    apiClient,
    workflow,
    getUIMetadata = () => ({}),
    activityDelay = 15000,
    fallbackInterval = 60000,
}: UseAutoSaveConfig) {
    const activityTimerRef = useRef<NodeJS.Timeout | null>(null);
    const fallbackTimerRef = useRef<NodeJS.Timeout | null>(null);
    const lastSaveAttemptRef = useRef<Date | null>(null);

    const { 
        autoSave, 
        markSaving, 
        markSaved, 
        markSaveError,
        getSpec 
    } = useWorkflowStore((state) => ({
        autoSave: state.autoSave,
        markSaving: state.markSaving,
        markSaved: state.markSaved,
        markSaveError: state.markSaveError,
        getSpec: state.getSpec,
    }));

    const performAutoSave = useCallback(async () => {
        if (!autoSave.autoSaveEnabled || autoSave.isSaving) return;

        try {
            markSaving();
            lastSaveAttemptRef.current = new Date();

            const spec = getSpec();
            const uiMetadata = getUIMetadata();

            await apiClient.saveWorkflowSpec(workflow, spec, uiMetadata, true); // isAutoSave = true
            
            markSaved();
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "Auto-save failed";
            markSaveError(errorMessage);
            console.error("Auto-save failed:", error);
        }
    }, [apiClient, workflow, autoSave.autoSaveEnabled, autoSave.isSaving, markSaving, markSaved, markSaveError, getSpec, getUIMetadata]);

    const scheduleActivitySave = useCallback(() => {
        // Clear existing activity timer
        if (activityTimerRef.current) {
            clearTimeout(activityTimerRef.current);
        }

        // Schedule save after activity delay (3s after last change)
        activityTimerRef.current = setTimeout(() => {
            if (autoSave.hasUnsavedChanges) performAutoSave();
        }, 3000); // 3 second delay after last activity
    }, [autoSave.hasUnsavedChanges, performAutoSave]);

    const scheduleFallbackSave = useCallback(() => {
        // Clear existing fallback timer
        if (fallbackTimerRef.current) {
            clearInterval(fallbackTimerRef.current);
        }

        // Schedule regular fallback saves
        fallbackTimerRef.current = setInterval(() => {
            if (autoSave.hasUnsavedChanges && autoSave.autoSaveEnabled) performAutoSave();
        }, fallbackInterval);
    }, [autoSave.hasUnsavedChanges, autoSave.autoSaveEnabled, fallbackInterval, performAutoSave]);

    // React to changes in workflow state
    useEffect(() => {
        if (autoSave.hasUnsavedChanges && autoSave.autoSaveEnabled) {
            scheduleActivitySave();
        }
    }, [autoSave.hasUnsavedChanges, autoSave.autoSaveEnabled, scheduleActivitySave]);

    // Set up fallback timer on mount
    useEffect(() => {
        if (autoSave.autoSaveEnabled) scheduleFallbackSave();

        return () => {
            if (fallbackTimerRef.current) clearInterval(fallbackTimerRef.current);
        };
    }, [autoSave.autoSaveEnabled, scheduleFallbackSave]);

    // Cleanup timers on unmount
    useEffect(() => {
        return () => {
            if (activityTimerRef.current) clearTimeout(activityTimerRef.current);
            if (fallbackTimerRef.current) clearInterval(fallbackTimerRef.current);
        };
    }, []);

    return {
        isAutoSaving: autoSave.isSaving,
        hasUnsavedChanges: autoSave.hasUnsavedChanges,
        lastSaved: autoSave.lastSaved,
        saveError: autoSave.saveError,
        autoSaveEnabled: autoSave.autoSaveEnabled,
        performManualSave: performAutoSave, // For manual save button
    };
}