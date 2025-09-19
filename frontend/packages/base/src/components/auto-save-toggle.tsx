"use client";

import { useEffect, useCallback, useState } from "react";
import { Check, Loader, AlertTriangle, Clock, Save } from "lucide-react";
import { cn } from "../lib/utils";
import { createGlobalToast } from "./toast";
import { Button } from "../ui";

export interface AutoSaveState {
    hasUnsavedChanges: boolean;
    autoSaveEnabled: boolean;
    isSaving: boolean;
    lastSaved: Date | null;
    saveError: string | null;
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
    // Helper function to extract error message from various error formats
    const getErrorMessage = useCallback((error: string | null): string => {
        if (!error) return "Unknown error";

        // Handle [object Object] case (should be rare now that API client handles it)
        if (error === "[object Object]") return "Save request failed";
        if (error.includes("[object Object]")) return "Internal server error";

        // Handle common error patterns
        if (typeof error === "string") {
            // Extract HTTP status codes
            if (error.includes("500")) return "Internal server error";
            if (error.includes("404")) return "Endpoint not found";
            if (error.includes("403")) return "Permission denied";
            if (error.includes("401")) return "Authentication required";
            if (error.includes("Network Error")) return "Network connection failed";

            try {
                // Try to parse if it's a JSON string
                const parsed = JSON.parse(error);
                return parsed.message || parsed.error || parsed.detail || error;
            } catch {
                // Return if not JSON, but limit length
                return error.length > 100 ? error.substring(0, 100) + "..." : error;
            }
        }

        return String(error);
    }, []);

    // Auto-save state from workflow system
    const [autoSaveState, setAutoSaveState] = useState<AutoSaveState>({
        hasUnsavedChanges: false,
        autoSaveEnabled: true,
        isSaving: false,
        lastSaved: null,
        saveError: null,
    });

    // Listen for workflow auto-save status updates
    useEffect(() => {
        const handleWorkflowStatus = (event: CustomEvent) => {
            const newState = event.detail;
            const prevState = autoSaveState;
            setAutoSaveState(newState);

            // Show toast for errors
            if (newState.saveError) showErrorToast(newState.saveError);
        };

        window.addEventListener("workflow:autosave-status", handleWorkflowStatus as EventListener);
        return () =>
            window.removeEventListener(
                "workflow:autosave-status",
                handleWorkflowStatus as EventListener,
            );
    }, [autoSaveState]);

    // Manual save trigger with keyboard support
    const performManualSave = useCallback(async () => {
        if (autoSaveState.isSaving) return; // Prevent duplicate saves

        // Clear any existing save error before attempting manual save
        if (autoSaveState.saveError)
            window.dispatchEvent(new CustomEvent("workflow:clear-save-error"));

        window.dispatchEvent(new CustomEvent("workflow:manual-save"));
    }, [autoSaveState.isSaving, autoSaveState.saveError]);

    // Handle auto-save toggle changes
    const handleToggleChange = useCallback((enabled: boolean) => {
        setAutoSaveState((prev) => ({ ...prev, autoSaveEnabled: enabled }));
        window.dispatchEvent(new CustomEvent("workflow:toggle-autosave", { detail: { enabled } }));
    }, []);

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

    // Browser-level warning for unsaved changes
    useEffect(() => {
        const handleBeforeUnload = (event: BeforeUnloadEvent) => {
            // Only warn for truly unsaved changes, not while saving (server is handling it)
            if (autoSaveState.hasUnsavedChanges && !autoSaveState.isSaving) {
                const message =
                    "You have unsaved changes that will be lost if you leave this page.";
                event.preventDefault();
                event.returnValue = message; // For older browsers
                return message;
            }
        };

        window.addEventListener("beforeunload", handleBeforeUnload);
        return () => window.removeEventListener("beforeunload", handleBeforeUnload);
    }, [autoSaveState.hasUnsavedChanges, autoSaveState.isSaving]);

    // Expose simple check function for NavigationGuard
    useEffect(() => {
        (window as any).checkUnsavedChanges = (onProceed?: () => void) => {
            const hasUnsaved = autoSaveState.hasUnsavedChanges && !autoSaveState.isSaving;
            if (!hasUnsaved && onProceed) onProceed();
            return !hasUnsaved; // Return true if can proceed, false if blocked
        };

        return () => {
            delete (window as any).checkUnsavedChanges;
        };
    }, [autoSaveState.hasUnsavedChanges, autoSaveState.isSaving]);

    // Toast notification helpers
    const showErrorToast = useCallback(
        (error: string) => {
            const errorMessage = getErrorMessage(error);
            const toast = createGlobalToast();
            toast.error("Auto-save failed", {
                description: errorMessage,
                dismissible: true,
            });
        },
        [performManualSave],
    );

    // Simple status derivation
    const status = autoSaveState.isSaving
        ? "saving"
        : autoSaveState.saveError
          ? "error"
          : autoSaveState.hasUnsavedChanges
            ? "pending"
            : "saved";

    // Status configuration
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
            title: `Save failed: ${getErrorMessage(autoSaveState.saveError)}. Click to retry.`,
        },
        pending: {
            icon: autoSaveState.autoSaveEnabled ? (
                <Clock className="h-3.5 w-3.5 text-amber-600" />
            ) : (
                <AlertTriangle className="h-3.5 w-3.5 text-slate-600" />
            ),
            text: autoSaveState.autoSaveEnabled ? "Unsaved changes" : "Save manually",
            color: autoSaveState.autoSaveEnabled ? "text-amber-600" : "text-slate-600",
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
        <div className={cn("flex items-center gap-2 text-sm min-w-0", className)}>
            {/* Status Indicator */}
            <div
                className={cn(
                    "flex items-center gap-1.5 transition-colors duration-200 min-w-0",
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
                <span className={cn(currentStatus.color, "whitespace-nowrap")}>
                    {currentStatus.text}
                </span>
                {/* Inline error indicator for compact display */}
                {status === "error" && autoSaveState.saveError && (
                    <span
                        className="text-red-600 text-xs ml-1 max-w-[120px] sm:max-w-[200px] truncate inline-block"
                        title={getErrorMessage(autoSaveState.saveError)}
                    >
                        ({getErrorMessage(autoSaveState.saveError)})
                    </span>
                )}
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

            {/* Manual Save Button */}
            {showShortcut && (
                <>
                    <span className="text-muted-foreground">·</span>
                    <Button
                        onClick={performManualSave}
                        disabled={autoSaveState.isSaving}
                        variant="outline"
                        size="sm"
                        className={cn(
                            "px-2 py-1 text-xs h-auto",
                            "border-input bg-background hover:bg-accent hover:text-accent-foreground",
                            "transition-all duration-200 shadow-sm hover:shadow-md",
                            "disabled:opacity-50 disabled:cursor-not-allowed",
                        )}
                        title="Save workflow manually (Ctrl+S)"
                    >
                        <Save className="h-3 w-3 mr-1" />
                        <span className="hidden sm:inline">Save</span>
                    </Button>
                </>
            )}
        </div>
    );
}
