"use client";

import React from "react";
import type { RunData, StepMetadataBase } from "@vulkanlabs/client-open";
import type { RunNodeLayout } from "./workflow/types";
import { EmptyRunInfo, SidebarSkeleton } from "./loading-states";

export function WorkflowSidebar({
    clickedNode,
    runData,
    isLoading = false,
}: {
    clickedNode: RunNodeLayout | null;
    runData?: RunData;
    isLoading?: boolean;
}) {
    if (isLoading) {
        return <SidebarSkeleton />;
    }

    if (!runData) {
        return <EmptyRunInfo />;
    }

    return (
        <div className="h-full bg-gray-50 overflow-auto">
            {clickedNode === null ? (
                <RunInfo runData={runData} />
            ) : (
                <NodeContent clickedNode={clickedNode} />
            )}
        </div>
    );
}

function RunInfo({ runData }: { runData: RunData }) {
    return (
        <div className="p-6 space-y-6">
            <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Run Information</h2>
                
                <div className="space-y-4">
                    <InfoCard label="Run ID">
                        <p className="mt-1 text-sm font-mono text-gray-900 break-all">
                            {runData.run_id}
                        </p>
                    </InfoCard>
                    
                    <InfoCard label="Last Updated">
                        <p className="mt-1 text-sm text-gray-900">
                            {formatDate(runData.last_updated_at)}
                        </p>
                    </InfoCard>
                    
                    <InfoCard label="Status">
                        <StatusBadge status={runData.status} />
                    </InfoCard>
                </div>
            </div>
        </div>
    );
}

function NodeContent({ clickedNode }: { clickedNode: RunNodeLayout | null }) {
    if (clickedNode === null) {
        return (
            <div className="p-6">
                <p className="text-gray-500 text-sm">No node selected</p>
            </div>
        );
    }

    const nodeStatus = getNodeStatus(clickedNode);

    return (
        <div className="p-6 space-y-6">
            <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Node Details</h2>
                
                <div className="space-y-4">
                    {/* Node Info Card */}
                    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <Label>Name</Label>
                                <p className="mt-1 text-sm font-medium text-gray-900">
                                    {clickedNode.data.label}
                                </p>
                            </div>
                            <div>
                                <Label>Type</Label>
                                <p className="mt-1 text-sm text-gray-900">
                                    {clickedNode.data.type}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Status and Duration Card */}
                    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <Label>Status</Label>
                                <NodeStatusBadge status={nodeStatus} />
                            </div>
                            <div>
                                <Label>Duration</Label>
                                <p className="mt-1 text-sm text-gray-900">
                                    {clickedNode.data.run?.metadata
                                        ? getRunDuration(clickedNode.data.run.metadata)
                                        : "N/A"}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Output Section */}
                    {clickedNode.data.run?.output && (
                        <OutputSection output={clickedNode.data.run.output} />
                    )}

                    {/* Error Section */}
                    {clickedNode.data.run?.metadata?.error && (
                        <ErrorSection error={clickedNode.data.run.metadata.error} />
                    )}
                </div>
            </div>
        </div>
    );
}

// Helper Components
function InfoCard({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
            <Label>{label}</Label>
            {children}
        </div>
    );
}

function Label({ children }: { children: React.ReactNode }) {
    return (
        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            {children}
        </label>
    );
}

function StatusBadge({ status }: { status?: string }) {
    const statusColors = {
        completed: 'bg-green-100 text-green-800',
        failed: 'bg-red-100 text-red-800',
        running: 'bg-blue-100 text-blue-800',
        default: 'bg-gray-100 text-gray-800'
    };

    const color = statusColors[status as keyof typeof statusColors] || statusColors.default;

    return (
        <p className="mt-1">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
                {status || 'Unknown'}
            </span>
        </p>
    );
}

function NodeStatusBadge({ status }: { status: string }) {
    const statusColors = {
        error: 'bg-red-100 text-red-800 border-red-200',
        success: 'bg-green-100 text-green-800 border-green-200',
        skipped: 'bg-gray-100 text-gray-800 border-gray-200'
    };

    return (
        <p className="mt-1">
            <span className={`
                inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                ${statusColors[status as keyof typeof statusColors]}
            `}>
                {status}
            </span>
        </p>
    );
}

function OutputSection({ output }: { output: any }) {
    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                <h3 className="text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Output
                </h3>
            </div>
            <div className="max-h-96 overflow-auto">
                <pre className="p-4 text-xs text-gray-700 font-mono">
                    {JSON.stringify(output, null, 2)}
                </pre>
            </div>
        </div>
    );
}

function ErrorSection({ error }: { error: string | Error }) {
    return (
        <div className="bg-red-50 rounded-lg shadow-sm border border-red-200 overflow-hidden">
            <div className="px-4 py-3 bg-red-100 border-b border-red-200">
                <h3 className="text-xs font-medium text-red-800 uppercase tracking-wider">
                    Error
                </h3>
            </div>
            <div className="p-4">
                <p className="text-sm text-red-700">
                    {typeof error === 'string' ? error : error.message}
                </p>
            </div>
        </div>
    );
}

// Utility Functions
function getNodeStatus(node: RunNodeLayout): string {
    // Input node is always considered successful if the run is executing
    if (node.id === 'input_node' || node.data.type === 'INPUT') {
        return 'success';
    }
    
    if (node.data.run?.metadata?.error) return 'error';
    if (node.data.run) return 'success';
    return 'skipped';
}

function formatDate(date: any): string {
    try {
        return date ? new Date(date).toLocaleString() : "N/A";
    } catch (error) {
        return date?.toString() || "N/A";
    }
}

function getRunDuration(metadata: StepMetadataBase): string {
    const start = new Date(metadata.start_time * 1000);
    const end = new Date(metadata.end_time * 1000);
    const duration = end.getTime() - start.getTime();
    
    const milliseconds = duration % 1000;
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
        return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else if (seconds > 0) {
        return `${seconds}s ${milliseconds}ms`;
    } else {
        return `${milliseconds}ms`;
    }
}