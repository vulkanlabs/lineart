"use client";

import { useState, useEffect } from "react";
import { Check, Loader, AlertTriangle, Clock } from "lucide-react";

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
}

/**
 * AutoSaveToggle - Navigation bar auto-save component
 * 
 * - Listens for workflow auto-save status via events
 * - Shows status with proper icons and colors
 * - Handles toggle and manual save commands
 * - Integrates with existing workflow system
 */
export function AutoSaveToggle({ className = "" }: AutoSaveToggleProps = {}) {
    const [currentTime, setCurrentTime] = useState<Date>(new Date());
    
    // Auto-save state from workflow system
    const [autoSaveState, setAutoSaveState] = useState<AutoSaveState>({
        hasUnsavedChanges: false,
        autoSaveEnabled: true,
        isSaving: false,
        lastSaved: null,
        saveError: null,
    });

    // Update current time every minute for relative timestamps
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentTime(new Date());
        }, 60000);
        return () => clearInterval(interval);
    }, []);

    // Listen for workflow auto-save status updates
    useEffect(() => {
        const handleWorkflowStatus = (event: CustomEvent) => {
            setAutoSaveState(event.detail);
        };

        window.addEventListener('workflow:autosave-status', handleWorkflowStatus as EventListener);

        return () => {
            window.removeEventListener('workflow:autosave-status', handleWorkflowStatus as EventListener);
        };
    }, []);

    // Handle auto-save toggle changes
    const handleToggleChange = (enabled: boolean) => {
        setAutoSaveState(prev => ({ ...prev, autoSaveEnabled: enabled }));
        
        // Send command to workflow system
        window.dispatchEvent(new CustomEvent('navigation:toggle-autosave', { 
            detail: { enabled } 
        }));
    };

    // Manual save trigger
    const performManualSave = async () => {
        // Send command to workflow system
        window.dispatchEvent(new CustomEvent('navigation:manual-save'));
    };

    // Derived state for UI
    const status = autoSaveState.isSaving ? 'saving' : 
                  autoSaveState.saveError ? 'error' :
                  autoSaveState.hasUnsavedChanges ? 'pending' : 
                  autoSaveState.lastSaved ? 'saved' : 'ready';

    const getStatusIcon = () => {
        switch (status) {
            case 'saving':
                return <Loader className="h-3.5 w-3.5 animate-spin text-blue-600" />;
            case 'error':
                return <AlertTriangle className="h-3.5 w-3.5 text-red-600" />;
            case 'pending':
                return <Clock className="h-3.5 w-3.5 text-orange-600" />;
            case 'saved':
                return <Check className="h-3.5 w-3.5 text-green-600" />;
            case 'ready':
                return <Check className="h-3.5 w-3.5 text-green-600" />;
            default:
                return null;
        }
    };

    const getStatusText = () => {
        switch (status) {
            case 'saving':
                return "Saving...";
            case 'error':
                return autoSaveState.saveError || "Failed to save";
            case 'pending':
                return "Unsaved changes";
            case 'saved':
                return getTimestampText();
            case 'ready':
                return "Ready to save";
            default:
                return "";
        }
    };

    const getTimestampText = () => {
        if (!autoSaveState.lastSaved) return "Ready to save";
        
        const diffMs = currentTime.getTime() - autoSaveState.lastSaved.getTime();
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMinutes / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMinutes < 1) return "Saved just now";
        if (diffMinutes < 60) return `Saved ${diffMinutes}m ago`;
        if (diffHours < 24) return `Saved ${diffHours}h ago`;
        if (diffDays === 1) return "Saved yesterday";
        return `Saved ${diffDays}d ago`;
    };

    const getTimestampOpacity = () => {
        if ((status !== 'saved' && status !== 'ready') || !autoSaveState.lastSaved) return "opacity-100";
        
        const diffMs = currentTime.getTime() - autoSaveState.lastSaved.getTime();
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        
        if (diffMinutes < 2) return "opacity-100";
        if (diffMinutes < 5) return "opacity-90";
        if (diffMinutes < 15) return "opacity-75";
        if (diffMinutes < 60) return "opacity-60";
        return "opacity-50";
    };

    const getStatusColor = () => {
        switch (status) {
            case 'saving':
                return "text-muted-foreground";
            case 'error':
                return "text-destructive";
            case 'pending':
                return "text-muted-foreground";
            case 'saved':
                return "text-muted-foreground";
            case 'ready':
                return "text-muted-foreground";
            default:
                return "text-muted-foreground";
        }
    };

    const statusIcon = getStatusIcon();
    const statusText = getStatusText();

    return (
        <div className={`flex items-center gap-2 text-sm ${className}`}>
            {statusIcon && (
                <>
                    <div 
                        className={`flex items-center gap-1.5 transition-opacity duration-300 ${getTimestampOpacity()}`}
                        onClick={status === 'error' ? performManualSave : undefined}
                        style={{ cursor: status === 'error' ? 'pointer' : 'default' }}
                        title={status === 'error' ? 'Click to retry save' : undefined}
                    >
                        {statusIcon}
                        {statusText && (
                            <span className={getStatusColor()}>
                                {statusText}
                            </span>
                        )}
                    </div>
                    <span className="text-muted-foreground">·</span>
                </>
            )}
            <span className="text-foreground">Autosave</span>
            <label className="flex items-center cursor-pointer">
                <input
                    type="checkbox"
                    checked={autoSaveState.autoSaveEnabled}
                    onChange={(e) => handleToggleChange(e.target.checked)}
                    className="sr-only"
                />
                <div className={`relative inline-flex h-3.5 w-6 rounded-full transition-all duration-200 ease-in-out ${
                    autoSaveState.autoSaveEnabled 
                        ? 'bg-primary' 
                        : 'bg-gray-300'
                }`}>
                    <div className={`inline-block h-2.5 w-2.5 transform rounded-full bg-white transition-all duration-200 ease-in-out mt-0.5 ${
                        autoSaveState.autoSaveEnabled 
                            ? 'translate-x-3' 
                            : 'translate-x-0.5'
                    }`} />
                </div>
            </label>
        </div>
    );
}
