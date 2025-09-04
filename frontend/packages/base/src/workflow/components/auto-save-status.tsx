"use client";

import { useEffect, useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { useWorkflowStore } from "../store/workflow-store";

/**
 * AutoSaveStatus - Synchronizes workflow auto-save state with navigation bar
 * 
 * - Listens to workflow auto-save state changes (saving, saved, errors, etc.)
 * - Dispatches custom events that the navigation bar can listen to
 * - Receives toggle/manual save commands from navigation and forwards to workflow
 * - Prevents false positives on initial page load
 */
export function AutoSaveStatus() {
    const { autoSave, toggleAutoSave } = useWorkflowStore(
        useShallow((state) => ({
            autoSave: state.autoSave,
            toggleAutoSave: state.toggleAutoSave,
        }))
    );

    // Track if this is the initial render to prevent false unsaved status
    const [isInitialRender, setIsInitialRender] = useState(true);

    // Mark as initialized after a short delay to allow page to settle
    useEffect(() => {
        const timer = setTimeout(() => {
            setIsInitialRender(false);
        }, 500); // Give workflow time to initialize properly
        
        return () => clearTimeout(timer);
    }, []);

    // Sync workflow auto-save state to navigation bar
    useEffect(() => {
        const event = new CustomEvent('workflow:autosave-status', {
            detail: {
                hasUnsavedChanges: isInitialRender ? false : autoSave.hasUnsavedChanges, // Prevent false positive
                autoSaveEnabled: autoSave.autoSaveEnabled,
                isSaving: autoSave.isSaving,
                lastSaved: autoSave.lastSaved,
                saveError: autoSave.saveError,
            }
        });
        window.dispatchEvent(event);
    }, [autoSave, isInitialRender]);

    // Handle commands from navigation bar
    useEffect(() => {
        const handleToggle = (event: CustomEvent) => {
            if (event.detail.enabled !== autoSave.autoSaveEnabled) {
                toggleAutoSave();
            }
        };

        const handleManualSave = () => {
            // Forward manual save request to workflow canvas
            const saveEvent = new CustomEvent('workflow:manual-save');
            window.dispatchEvent(saveEvent);
        };

        window.addEventListener('navigation:toggle-autosave', handleToggle as EventListener);
        window.addEventListener('navigation:manual-save', handleManualSave);

        return () => {
            window.removeEventListener('navigation:toggle-autosave', handleToggle as EventListener);
            window.removeEventListener('navigation:manual-save', handleManualSave);
        };
    }, [autoSave.autoSaveEnabled, toggleAutoSave]);

    return null; // No UI - this is a data synchronization component
}
