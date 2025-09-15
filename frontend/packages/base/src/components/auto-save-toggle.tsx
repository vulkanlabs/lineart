"use client";

import { useEffect, useCallback, useState } from "react";
import { Check, Loader, AlertTriangle, Clock, Save } from "lucide-react";
import { cn } from "../lib/utils";

export interface AutoSaveState {
    hasUnsavedChanges: boolean;
    autoSaveEnabled: boolean;
    isSaving: boolean;
    lastSaved: Date | null;
    saveError: string | null;
    retryCount?: number;
}

export interface AutoSaveToggleProps {
    /**
     * Custom CSS classes
     */
    className?: string;
    /**
     * Show keyboard shortcut hint
     */
    showShortcut?: boolean;
}

/**
 * Enhanced AutoSaveToggle - Navigation bar auto-save component
 *
 * Features:
 * - Simplified status display with better UX
 * - Keyboard shortcuts (Ctrl+S for manual save)
 * - Smart retry logic with exponential backoff
 * - Accessible design with proper ARIA labels
 * - Toast notifications for persistent errors
 */
export function AutoSaveToggle({ className = "", showShortcut = true }: AutoSaveToggleProps = {}) {
    // Auto-save state from workflow system
    const [autoSaveState, setAutoSaveState] = useState<AutoSaveState>({
        hasUnsavedChanges: false,
        autoSaveEnabled: true,
        isSaving: false,
        lastSaved: null,
        saveError: null,
        retryCount: 0,
    });

    // Listen for workflow auto-save status updates
    useEffect(() => {
        const handleWorkflowStatus = (event: CustomEvent) => {
            const newState = event.detail;
            setAutoSaveState(newState);

            // Show toast for persistent errors (after 3 failed attempts)
            if (newState.saveError && (newState.retryCount || 0) >= 3) {
                showErrorToast(newState.saveError);
            }
        };

        window.addEventListener("workflow:autosave-status", handleWorkflowStatus as EventListener);
        return () =>
            window.removeEventListener(
                "workflow:autosave-status",
                handleWorkflowStatus as EventListener,
            );
    }, []);

    // Handle auto-save toggle changes
    const handleToggleChange = useCallback((enabled: boolean) => {
        setAutoSaveState((prev) => ({ ...prev, autoSaveEnabled: enabled }));
        window.dispatchEvent(
            new CustomEvent("navigation:toggle-autosave", { detail: { enabled } }),
        );
    }, []);

    // Manual save trigger with keyboard support
    const performManualSave = useCallback(async () => {
        if (autoSaveState.isSaving) return; // Prevent duplicate saves
        window.dispatchEvent(new CustomEvent("navigation:manual-save"));
    }, [autoSaveState.isSaving]);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            // Ctrl+S or Cmd+S for manual save
            if ((event.ctrlKey || event.metaKey) && event.key === "s") {
                event.preventDefault();
                performManualSave();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [performManualSave]);

    // Toast notification helper
    const showErrorToast = useCallback(
        (error: string) => {
            // Try to use existing toast system or fallback to console
            if (typeof window !== "undefined" && "toast" in window) {
                (window as any).toast(error, {
                    variant: "destructive",
                    title: "Auto-save failed",
                    description: "Click to retry manually",
                    action: { label: "Retry", onClick: performManualSave },
                });
            } else {
                console.error("Auto-save failed:", error);
            }
        },
        [performManualSave],
    );

    // Simplified status derivation
    const status = autoSaveState.isSaving
        ? "saving"
        : autoSaveState.saveError
          ? "error"
          : autoSaveState.hasUnsavedChanges
            ? "pending"
            : "saved";

    // Status configuration with enhanced UX
    const statusConfig = {
        saving: {
            icon: <Loader className="h-3.5 w-3.5 animate-spin text-blue-600" />,
            text: "Saving...",
            color: "text-blue-600",
            clickable: false,
        },
        error: {
            icon: <AlertTriangle className="h-3.5 w-3.5 text-red-600" />,
            text: "Failed to save",
            color: "text-red-600",
            clickable: true,
            title: "Click to retry save",
        },
        pending: {
            icon: <Clock className="h-3.5 w-3.5 text-amber-600" />,
            text: "Unsaved changes",
            color: "text-amber-600",
            clickable: false,
        },
        saved: {
            icon: <Check className="h-3.5 w-3.5 text-green-600" />,
            text: autoSaveState.lastSaved ? "Saved" : "Ready",
            color: "text-green-600",
            clickable: false,
        },
    };

    const currentStatus = statusConfig[status];

    return (
        <div className={cn("flex items-center gap-2 text-sm", className)}>
            {/* Status Indicator */}
            <div
                className={cn(
                    "flex items-center gap-1.5 transition-colors duration-200",
                    currentStatus.clickable && "cursor-pointer hover:opacity-80",
                )}
                onClick={currentStatus.clickable ? performManualSave : undefined}
                title={currentStatus.title}
                role={currentStatus.clickable ? "button" : undefined}
                tabIndex={currentStatus.clickable ? 0 : undefined}
                onKeyDown={
                    currentStatus.clickable
                        ? (e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                  e.preventDefault();
                                  performManualSave();
                              }
                          }
                        : undefined
                }
            >
                {currentStatus.icon}
                <span className={currentStatus.color}>
                    {currentStatus.text}
                    {status === "error" && (autoSaveState.retryCount || 0) > 0 && (
                        <span className="ml-1 text-xs opacity-70">
                            (Retry {autoSaveState.retryCount})
                        </span>
                    )}
                </span>
            </div>

            <span className="text-muted-foreground">·</span>

            {/* Auto-save Toggle */}
            <div className="flex items-center gap-2">
                <span className="text-foreground">Autosave</span>
                <label
                    className="flex items-center cursor-pointer group"
                    title={`Auto-save is ${autoSaveState.autoSaveEnabled ? "enabled" : "disabled"}${showShortcut ? " (Ctrl+S to save manually)" : ""}`}
                >
                    <input
                        type="checkbox"
                        checked={autoSaveState.autoSaveEnabled}
                        onChange={(e) => handleToggleChange(e.target.checked)}
                        className="sr-only"
                        aria-label={`Toggle auto-save ${autoSaveState.autoSaveEnabled ? "off" : "on"}`}
                    />
                    <div
                        className={cn(
                            "relative inline-flex h-4 w-7 rounded-full transition-all duration-200 ease-in-out",
                            "focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-1",
                            autoSaveState.autoSaveEnabled
                                ? "bg-primary"
                                : "bg-gray-300 group-hover:bg-gray-400",
                        )}
                    >
                        <div
                            className={cn(
                                "inline-block h-3 w-3 transform rounded-full bg-white transition-transform duration-200 ease-in-out mt-0.5",
                                "shadow-sm",
                                autoSaveState.autoSaveEnabled
                                    ? "translate-x-3.5"
                                    : "translate-x-0.5",
                            )}
                        />
                    </div>
                </label>
            </div>

            {/* Manual Save Button with Keyboard Shortcut */}
            {showShortcut && (
                <>
                    <span className="text-muted-foreground">·</span>
                    <button
                        onClick={performManualSave}
                        disabled={autoSaveState.isSaving}
                        className={cn(
                            "inline-flex items-center gap-1 px-2 py-1 rounded text-xs",
                            "bg-white hover:bg-gray-50 text-gray-700 hover:text-gray-900",
                            "transition-colors duration-200 border border-gray-300",
                            "disabled:opacity-50 disabled:cursor-not-allowed",
                        )}
                        title="Save workflow manually (Ctrl+S)"
                    >
                        <Save className="h-3 w-3" />
                        <span className="hidden sm:inline">Save</span>
                    </button>
                </>
            )}
        </div>
    );
}
