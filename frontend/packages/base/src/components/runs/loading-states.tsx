"use client";

import React from "react";
import { Loader2, AlertCircle, Workflow, FileText } from "lucide-react";

// Skeleton Components
export function SkeletonBox({ className = "" }: { className?: string }) {
    return (
        <div className={`bg-gray-200 animate-pulse rounded ${className}`} />
    );
}

export function SkeletonText({ 
    lines = 1, 
    className = "" 
}: { 
    lines?: number; 
    className?: string;
}) {
    return (
        <div className={`space-y-2 ${className}`}>
            {Array.from({ length: lines }, (_, i) => (
                <div
                    key={i}
                    className={`bg-gray-200 animate-pulse rounded h-4 ${
                        i === lines - 1 ? 'w-3/4' : 'w-full'
                    }`}
                />
            ))}
        </div>
    );
}

// Loading States
export function WorkflowSkeleton() {
    return (
        <div className="h-full bg-white p-6 flex items-center justify-center">
            <div className="text-center">
                <div className="mb-4">
                    <Workflow size={48} className="mx-auto text-gray-300 animate-pulse" />
                </div>
                <SkeletonText lines={2} className="w-48 mx-auto" />
            </div>
        </div>
    );
}

export function SidebarSkeleton() {
    return (
        <div className="h-full bg-gray-50 p-6 space-y-6">
            {/* Header skeleton */}
            <div>
                <SkeletonBox className="h-6 w-32 mb-4" />
                
                {/* Cards skeleton */}
                <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                            <SkeletonBox className="h-3 w-16 mb-2" />
                            <SkeletonBox className="h-4 w-full" />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export function LogsTableSkeleton() {
    return (
        <div className="flex flex-col h-full">
            {/* Toolbar skeleton */}
            <div className="bg-white border-b border-gray-200 px-4 py-3">
                <div className="flex items-center gap-3">
                    <SkeletonBox className="h-9 flex-1 max-w-md" />
                    <SkeletonBox className="h-9 w-20" />
                    <SkeletonBox className="h-4 w-24" />
                </div>
            </div>

            {/* Table skeleton */}
            <div className="flex-1 p-4">
                <div className="space-y-3">
                    {/* Header */}
                    <div className="grid grid-cols-5 gap-4 pb-2 border-b border-gray-200">
                        {[1, 2, 3, 4, 5].map((i) => (
                            <SkeletonBox key={i} className="h-3 w-20" />
                        ))}
                    </div>
                    
                    {/* Rows */}
                    {Array.from({ length: 8 }, (_, i) => (
                        <div key={i} className="grid grid-cols-5 gap-4 py-2">
                            <SkeletonBox className="h-4 w-24" />
                            <SkeletonBox className="h-4 w-16" />
                            <SkeletonBox className="h-4 w-12" />
                            <SkeletonBox className="h-4 w-full" />
                            <SkeletonBox className="h-4 w-14" />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

// Loading Overlay
export function LoadingOverlay({ 
    message = "Loading...",
    className = ""
}: { 
    message?: string;
    className?: string;
}) {
    return (
        <div className={`
            absolute inset-0 bg-white/90 backdrop-blur-sm 
            flex items-center justify-center z-50
            ${className}
        `}>
            <div className="text-center">
                <Loader2 size={32} className="mx-auto mb-3 text-blue-600 animate-spin" />
                <p className="text-sm text-gray-600">{message}</p>
            </div>
        </div>
    );
}

// Empty States
export function EmptyWorkflow() {
    return (
        <div className="h-full bg-white flex items-center justify-center p-8">
            <div className="text-center max-w-md">
                <Workflow size={64} className="mx-auto mb-6 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Workflow Available
                </h3>
                <p className="text-gray-500 mb-6">
                    This run doesn't have an associated workflow to display. 
                    The workflow visualization will appear here once data is available.
                </p>
                <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-xs text-gray-600">
                        <strong>Tip:</strong> Workflow nodes will show execution status, 
                        duration, and allow you to inspect individual step details.
                    </p>
                </div>
            </div>
        </div>
    );
}

export function EmptyRunInfo() {
    return (
        <div className="h-full bg-gray-50 flex items-center justify-center p-8">
            <div className="text-center max-w-sm">
                <FileText size={48} className="mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Run Data
                </h3>
                <p className="text-gray-500">
                    Run information will be displayed here once the data loads.
                </p>
            </div>
        </div>
    );
}

// Error States
export function ErrorState({ 
    title = "Something went wrong",
    message = "An error occurred while loading data. Please try refreshing the page.",
    onRetry
}: {
    title?: string;
    message?: string;
    onRetry?: () => void;
}) {
    return (
        <div className="h-full flex items-center justify-center p-8">
            <div className="text-center max-w-md">
                <AlertCircle size={64} className="mx-auto mb-6 text-red-400" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {title}
                </h3>
                <p className="text-gray-500 mb-6">
                    {message}
                </p>
                {onRetry && (
                    <button
                        onClick={onRetry}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Try Again
                    </button>
                )}
            </div>
        </div>
    );
}

// Inline loading indicators
export function InlineLoader({ size = 16, className = "" }: { size?: number; className?: string }) {
    return (
        <Loader2 size={size} className={`animate-spin text-gray-400 ${className}`} />
    );
}

export function LoadingDots({ className = "" }: { className?: string }) {
    return (
        <div className={`inline-flex space-x-1 ${className}`}>
            <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
    );
}