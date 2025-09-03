"use client";

import React, { useState } from "react";
import {
    Info,
    Clock,
    CheckCircle,
    XCircle,
    Play,
    Database,
    Tag,
    ChevronDown,
    Copy,
    Check,
    Loader2,
    Settings,
    FileText,
    AlertCircle,
} from "lucide-react";

import type { RunData, StepMetadataBase, RunStatus } from "@vulkanlabs/client-open";
import { RunStatus as RunStatusValues } from "@vulkanlabs/client-open";

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
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["input"]));

    const toggleSection = (section: string) => {
        setExpandedSections((prev) => {
            const next = new Set(prev);
            if (next.has(section)) {
                next.delete(section);
            } else {
                next.add(section);
            }
            return next;
        });
    };

    return (
        <div className="flex flex-col h-full">
            {/* Clean Header */}
            <div className="px-6 py-4 border-b border-gray-200 bg-white">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">Run Details</h2>
                    <StatusBadge status={runData.status} />
                </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto">
                <div className="p-4 space-y-4">
                    {/* Key Information Section */}
                    <section>
                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center">
                            <Info className="w-3.5 h-3.5 mr-1.5" />
                            Identification
                        </h3>
                        <div className="bg-white rounded-lg border border-gray-200 p-4">
                            <div className="grid grid-cols-2 gap-4">
                                <IdDisplay label="Run ID" id={runData.run_id} />
                                {runData.policy_version_id && (
                                    <IdDisplay
                                        label="Policy Version"
                                        id={runData.policy_version_id}
                                    />
                                )}
                            </div>
                        </div>
                    </section>

                    {/* Timing Section */}
                    <section>
                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center">
                            <Clock className="w-3.5 h-3.5 mr-1.5" />
                            Timing
                        </h3>
                        <div className="bg-white rounded-lg border border-gray-200 p-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <span className="text-xs text-gray-500">Started</span>
                                    <p className="text-sm text-gray-900 mt-0.5">
                                        {runData.started_at
                                            ? formatDate(runData.started_at)
                                            : "Not started"}
                                    </p>
                                </div>
                                <div>
                                    <span className="text-xs text-gray-500">Duration</span>
                                    <p className="text-sm font-medium text-gray-900 mt-0.5">
                                        {getRunDurationFromData(runData)}
                                    </p>
                                </div>
                            </div>
                            {runData.status === RunStatusValues.Started && (
                                <div className="mt-3 pt-3 border-t border-gray-100">
                                    <div className="flex items-center text-xs text-blue-600">
                                        <Loader2 className="animate-spin h-2.5 w-2.5 mr-1.5" />
                                        Currently running...
                                    </div>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Result Section */}
                    {runData.result && (
                        <section>
                            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center">
                                <CheckCircle className="w-3.5 h-3.5 mr-1.5" />
                                Result
                            </h3>
                            <div className="bg-white rounded-lg border border-gray-200 p-4">
                                <p className="text-sm text-gray-900">{runData.result}</p>
                            </div>
                        </section>
                    )}

                    {/* Collapsible Data Sections */}
                    {runData.input_data && (
                        <CollapsibleSection
                            title="Input Data"
                            icon="database"
                            isExpanded={expandedSections.has("input")}
                            onToggle={() => toggleSection("input")}
                            isEmpty={
                                !runData.input_data || Object.keys(runData.input_data).length === 0
                            }
                        >
                            <JsonDisplay data={runData.input_data} />
                        </CollapsibleSection>
                    )}

                    {runData.run_metadata && (
                        <CollapsibleSection
                            title="Metadata"
                            icon="tag"
                            isExpanded={expandedSections.has("metadata")}
                            onToggle={() => toggleSection("metadata")}
                            isEmpty={
                                !runData.run_metadata ||
                                Object.keys(runData.run_metadata).length === 0
                            }
                        >
                            <JsonDisplay data={runData.run_metadata} />
                        </CollapsibleSection>
                    )}
                </div>
            </div>
        </div>
    );
}

function NodeContent({ clickedNode }: { clickedNode: RunNodeLayout | null }) {
    if (clickedNode === null) {
        return (
            <div className="flex flex-col h-full">
                {/* Clean Header */}
                <div className="px-6 py-4 border-b border-gray-200 bg-white">
                    <h2 className="text-lg font-semibold text-gray-900">Node Details</h2>
                </div>

                {/* Empty State */}
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <Settings className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500 text-sm">No node selected</p>
                        <p className="text-gray-400 text-xs mt-1">
                            Click on a node to see its details
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    const nodeStatus = getNodeStatus(clickedNode);

    return (
        <div className="flex flex-col h-full">
            {/* Clean Header */}
            <div className="px-6 py-4 border-b border-gray-200 bg-white">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">Node Details</h2>
                    <NodeStatusBadge status={nodeStatus} />
                </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto">
                <div className="p-4 space-y-4">
                    {/* Node Information Section */}
                    <section>
                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center">
                            <Settings className="w-3.5 h-3.5 mr-1.5" />
                            Node Information
                        </h3>
                        <div className="bg-white rounded-lg border border-gray-200 p-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <span className="text-xs text-gray-500">Name</span>
                                    <p
                                        className="text-sm font-medium text-gray-900 mt-0.5 truncate"
                                        title={clickedNode.data.label}
                                    >
                                        {clickedNode.data.label}
                                    </p>
                                </div>
                                <div>
                                    <span className="text-xs text-gray-500">Type</span>
                                    <p className="text-sm text-gray-900 mt-0.5">
                                        {clickedNode.data.type}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Execution Section */}
                    {clickedNode.data.run && (
                        <section>
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center">
                                    <Clock className="w-3.5 h-3.5 mr-1.5" />
                                    Execution
                                </h3>
                                <span className="text-xs font-medium text-gray-700 bg-gray-50 px-2 py-1 rounded">
                                    {clickedNode.data.run.metadata
                                        ? getRunDuration(clickedNode.data.run.metadata)
                                        : "N/A"}
                                </span>
                            </div>
                        </section>
                    )}

                    {/* Output Section */}
                    {clickedNode.data.run?.output && (
                        <section>
                            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center">
                                <FileText className="w-3.5 h-3.5 mr-1.5" />
                                Output
                            </h3>
                            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                                <div className="max-h-96 overflow-auto">
                                    <pre className="p-4 text-xs text-gray-700 font-mono">
                                        {JSON.stringify(clickedNode.data.run.output, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        </section>
                    )}

                    {/* Error Section */}
                    {clickedNode.data.run?.metadata?.error && (
                        <section>
                            <h3 className="text-xs font-semibold text-red-600 uppercase tracking-wider mb-2 flex items-center">
                                <AlertCircle className="w-3.5 h-3.5 mr-1.5" />
                                Error
                            </h3>
                            <div className="bg-red-50 rounded-lg border border-red-200 p-4">
                                <p className="text-sm text-red-700">
                                    {typeof clickedNode.data.run.metadata.error === "string"
                                        ? clickedNode.data.run.metadata.error
                                        : clickedNode.data.run.metadata.error.message}
                                </p>
                            </div>
                        </section>
                    )}
                </div>
            </div>
        </div>
    );
}

// Helper Components
function IdDisplay({
    label,
    id,
    className = "",
}: {
    label: string;
    id: string;
    className?: string;
}) {
    const [copied, setCopied] = useState(false);
    const [showTooltip, setShowTooltip] = useState(false);

    const truncatedId = id.length > 8 ? `${id.substring(0, 8)}...` : id;

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(id);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy ID:", err);
        }
    };

    return (
        <div className={className}>
            <span className="text-xs text-gray-500">{label}</span>
            <div className="mt-0.5 flex items-center justify-between">
                <div
                    className="relative"
                    onMouseEnter={() => setShowTooltip(true)}
                    onMouseLeave={() => setShowTooltip(false)}
                >
                    <span className="text-sm font-mono text-gray-900 cursor-help">
                        {truncatedId}
                    </span>

                    {/* Tooltip */}
                    {showTooltip && (
                        <div className="absolute bottom-full left-0 mb-2 z-50">
                            <div className="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                                {id}
                                <div className="absolute top-full left-2 w-0 h-0 border-l-2 border-r-2 border-t-2 border-l-transparent border-r-transparent border-t-gray-900"></div>
                            </div>
                        </div>
                    )}
                </div>

                <button
                    onClick={handleCopy}
                    className="ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                    title="Copy ID"
                >
                    {copied ? (
                        <Check className="w-2.5 h-2.5 text-green-500" />
                    ) : (
                        <Copy className="w-2.5 h-2.5" />
                    )}
                </button>
            </div>
        </div>
    );
}

function CollapsibleSection({
    title,
    icon,
    isExpanded,
    onToggle,
    children,
    isEmpty = false,
}: {
    title: string;
    icon: string;
    isExpanded: boolean;
    onToggle: () => void;
    children: React.ReactNode;
    isEmpty?: boolean;
}) {
    const getIcon = () => {
        switch (icon) {
            case "database":
                return Database;
            case "tag":
                return Tag;
            default:
                return Info;
        }
    };

    const IconComponent = getIcon();

    return (
        <section>
            <button
                onClick={onToggle}
                className="w-full flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 hover:text-gray-700 transition-colors"
            >
                <span className="flex items-center">
                    <IconComponent className="w-3.5 h-3.5 mr-1.5" />
                    {title}
                    {isEmpty && <span className="ml-2 text-gray-400 normal-case">(empty)</span>}
                </span>
                <ChevronDown
                    className={`w-3.5 h-3.5 transform transition-transform ${isExpanded ? "rotate-180" : ""}`}
                />
            </button>
            {isExpanded && !isEmpty && (
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                    {children}
                </div>
            )}
        </section>
    );
}

function JsonDisplay({ data }: { data: any }) {
    return (
        <div className="max-h-96 overflow-auto">
            <pre className="p-4 text-xs font-mono">
                <code>{JSON.stringify(data, null, 2)}</code>
            </pre>
        </div>
    );
}

function StatusBadge({ status }: { status?: RunStatus }) {
    const statusConfig: Record<
        RunStatus,
        { color: string; Icon: React.ComponentType<{ className?: string }> }
    > = {
        [RunStatusValues.Success]: {
            color: "bg-green-100 text-green-800 border-green-300",
            Icon: CheckCircle,
        },
        [RunStatusValues.Failure]: {
            color: "bg-red-100 text-red-800 border-red-300",
            Icon: XCircle,
        },
        [RunStatusValues.Started]: {
            color: "bg-blue-100 text-blue-800 border-blue-300",
            Icon: Play,
        },
        [RunStatusValues.Pending]: {
            color: "bg-yellow-100 text-yellow-800 border-yellow-300",
            Icon: Clock,
        },
    };

    const defaultConfig = {
        color: "bg-gray-100 text-gray-800 border-gray-300",
        Icon: Info,
    };

    const config = (status && statusConfig[status]) || defaultConfig;
    const { Icon } = config;

    return (
        <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.color}`}
        >
            <Icon className="w-2.5 h-2.5 mr-1" />
            {status || "Unknown"}
        </span>
    );
}

function NodeStatusBadge({ status }: { status: string }) {
    const getStatusConfig = () => {
        switch (status) {
            case "SUCCESS":
                return {
                    color: "bg-green-100 text-green-800 border-green-300",
                    Icon: CheckCircle,
                };
            case "ERROR":
                return {
                    color: "bg-red-100 text-red-800 border-red-300",
                    Icon: XCircle,
                };
            case "SKIPPED":
                return {
                    color: "bg-gray-100 text-gray-800 border-gray-300",
                    Icon: Info,
                };
            default:
                return {
                    color: "bg-gray-100 text-gray-800 border-gray-300",
                    Icon: Info,
                };
        }
    };

    const { color, Icon } = getStatusConfig();

    return (
        <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${color}`}
        >
            <Icon className="w-2.5 h-2.5 mr-1" />
            {status}
        </span>
    );
}

// Utility Functions
function getNodeStatus(node: RunNodeLayout): string {
    // Input node is always considered successful if the run is executing
    if (node.id === "input_node" || node.data.type === "INPUT") {
        return "SUCCESS";
    }

    if (node.data.run?.metadata?.error) return "ERROR";
    if (node.data.run) return "SUCCESS";
    return "SKIPPED";
}

function formatDate(date: any): string {
    try {
        return date ? new Date(date).toLocaleString() : "N/A";
    } catch (error) {
        return date?.toString() || "N/A";
    }
}

function formatDuration(durationMs: number): string {
    const milliseconds = durationMs % 1000;
    const seconds = Math.floor(durationMs / 1000);
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

function getRunDuration(metadata: StepMetadataBase): string {
    const start = new Date(metadata.start_time * 1000);
    const end = new Date(metadata.end_time * 1000);
    const duration = end.getTime() - start.getTime();
    return formatDuration(duration);
}

function getRunDurationFromData(runData: RunData): string {
    if (!runData.started_at) {
        return "Not started";
    }

    const start = new Date(runData.started_at);
    const end =
        runData.status === RunStatusValues.Started ? new Date() : new Date(runData.last_updated_at);
    const duration = end.getTime() - start.getTime();
    return formatDuration(duration);
}
