"use client";

import React from "react";
import { CheckCircle, AlertCircle, Clock, CloudOff } from "lucide-react";

interface AutoSaveStatusProps {
    isAutoSaving: boolean;
    hasUnsavedChanges: boolean;
    lastSaved: Date | null;
    saveError: string | null;
    autoSaveEnabled: boolean;
    retryAttempts: number;
    circuitBreakerOpen: boolean;
    consecutiveFailures: number;
    className?: string;
}

export function AutoSaveStatus({
    isAutoSaving,
    hasUnsavedChanges,
    lastSaved,
    saveError,
    autoSaveEnabled,
    retryAttempts,
    circuitBreakerOpen,
    consecutiveFailures,
    className = "",
}: AutoSaveStatusProps) {
    const formatTimeAgo = (date: Date): string => {
        const now = new Date();
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

        if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        return `${Math.floor(diffInSeconds / 3600)}h ago`;
    };

    const getStatusInfo = () => {
        if (!autoSaveEnabled) {
            return {
                icon: CloudOff,
                text: "Auto-save disabled",
                className: "text-gray-500",
                description: "Auto-save is currently disabled",
            };
        }

        if (circuitBreakerOpen) {
            return {
                icon: AlertCircle,
                text: "Auto-save paused",
                className: "text-orange-500",
                description: `Service temporarily unavailable (${consecutiveFailures} failures)`,
            };
        }

        if (isAutoSaving) {
            return {
                icon: Clock,
                text: retryAttempts > 0 ? `Saving (attempt ${retryAttempts + 1})...` : "Saving...",
                className: "text-blue-500 animate-pulse",
                description: "Saving your changes automatically",
            };
        }

        if (saveError) {
            return {
                icon: AlertCircle,
                text: "Save failed",
                className: "text-red-500",
                description: saveError,
            };
        }

        if (hasUnsavedChanges) {
            return {
                icon: Clock,
                text: "Unsaved changes",
                className: "text-orange-500",
                description: "Changes will be saved automatically",
            };
        }

        if (lastSaved) {
            return {
                icon: CheckCircle,
                text: `Saved ${formatTimeAgo(lastSaved)}`,
                className: "text-green-500",
                description: "All changes saved automatically",
            };
        }

        return {
            icon: CheckCircle,
            text: "All saved",
            className: "text-green-500",
            description: "No changes to save",
        };
    };

    const statusInfo = getStatusInfo();
    const StatusIcon = statusInfo.icon;

    return (
        <div className={`flex items-center space-x-2 ${className}`} title={statusInfo.description}>
            <StatusIcon className={`w-4 h-4 ${statusInfo.className}`} />
            <span className={`text-sm ${statusInfo.className}`}>{statusInfo.text}</span>
        </div>
    );
}

interface AutoSaveTooltipProps extends AutoSaveStatusProps {
    children: React.ReactNode;
}

interface AutoSaveIndicatorProps extends AutoSaveStatusProps {
    compact?: boolean;
}

export function AutoSaveIndicator({ compact = false, ...props }: AutoSaveIndicatorProps) {
    const {
        isAutoSaving,
        hasUnsavedChanges,
        lastSaved,
        saveError,
        autoSaveEnabled,
        retryAttempts,
        circuitBreakerOpen,
        consecutiveFailures,
        className = "",
    } = props;

    const getCompactStatusInfo = () => {
        if (!autoSaveEnabled) return { icon: CloudOff, className: "text-gray-400" };
        if (circuitBreakerOpen) return { icon: AlertCircle, className: "text-orange-500" };
        if (isAutoSaving) return { icon: Clock, className: "text-blue-500 animate-pulse" };
        if (saveError) return { icon: AlertCircle, className: "text-red-500" };
        if (hasUnsavedChanges) return { icon: Clock, className: "text-orange-500" };
        if (lastSaved) return { icon: CheckCircle, className: "text-green-500" };

        return { icon: CheckCircle, className: "text-green-500" };
    };

    if (compact) {
        const statusInfo = getCompactStatusInfo();
        const StatusIcon = statusInfo.icon;
        return (
            <AutoSaveTooltip {...props}>
                <StatusIcon className={`w-4 h-4 ${statusInfo.className} ${className}`} />
            </AutoSaveTooltip>
        );
    }

    return <AutoSaveStatus {...props} />;
}

export function AutoSaveTooltip({ children, ...statusProps }: AutoSaveTooltipProps) {
    const {
        isAutoSaving,
        hasUnsavedChanges,
        lastSaved,
        saveError,
        autoSaveEnabled,
        retryAttempts,
        circuitBreakerOpen,
        consecutiveFailures,
    } = statusProps;

    const getDetailedStatus = () => {
        const status = [];

        if (!autoSaveEnabled) {
            status.push("Auto-save is disabled");
        } else if (circuitBreakerOpen) {
            status.push(`Auto-save paused due to ${consecutiveFailures} consecutive failures`);
            status.push("Will resume automatically in a few minutes");
        } else if (isAutoSaving) {
            if (retryAttempts > 0) {
                status.push(`Saving attempt ${retryAttempts + 1}/3...`);
            } else {
                status.push("Saving your changes...");
            }
        } else if (saveError) {
            status.push(`Save error: ${saveError}`);
        } else if (hasUnsavedChanges) {
            status.push("Unsaved changes detected");
            status.push("Will auto-save in 3-15 seconds");
        } else if (lastSaved) {
            status.push(`Last saved: ${lastSaved.toLocaleString()}`);
        }

        return status;
    };

    const detailedStatus = getDetailedStatus();

    return (
        <div className="group relative">
            {children}
            {detailedStatus.length > 0 && (
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50">
                    {detailedStatus.map((line, index) => (
                        <div key={index}>{line}</div>
                    ))}
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-2 border-r-2 border-t-2 border-transparent border-t-gray-900"></div>
                </div>
            )}
        </div>
    );
}
