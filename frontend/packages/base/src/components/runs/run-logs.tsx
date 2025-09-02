"use client";

import React, { useState, useMemo } from "react";
import { Search, Filter, X, AlertCircle, Info, AlertTriangle, Bug } from "lucide-react";

import type { RunLogs } from "@vulkanlabs/client-open";

import { NodeLayoutConfig } from "./workflow/types";
import { LogsTableSkeleton } from "./loading-states";

type LogLevel = 'error' | 'warning' | 'info' | 'debug' | string;

export function LogsTable({
    runLogs,
    clickedNode,
    tableClass = "w-full",
    enableResponsiveColumns = true,
    isLoading = false,
}: {
    runLogs?: RunLogs;
    clickedNode: NodeLayoutConfig | null;
    tableClass?: "w-full" | "min-w-full";
    enableResponsiveColumns?: boolean;
    isLoading?: boolean;
}) {
    if (isLoading) {
        return <LogsTableSkeleton />;
    }

    if (!runLogs) {
        return (
            <div className="flex flex-col h-full">
                <div className="flex-1 flex items-center justify-center p-8">
                    <div className="text-center">
                        <Info size={48} className="mx-auto mb-4 text-gray-300" />
                        <p className="text-lg font-medium text-gray-900 mb-2">No logs available</p>
                        <p className="text-gray-500">Logs will appear here once the workflow runs</p>
                    </div>
                </div>
            </div>
        );
    }
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedLevels, setSelectedLevels] = useState<Set<LogLevel>>(new Set());
    const [showFilters, setShowFilters] = useState(false);

    // Get unique log levels for filter buttons
    const availableLevels = useMemo(() => {
        const levels = new Set<LogLevel>();
        runLogs.logs.forEach(log => {
            if (log.event.level) {
                levels.add(log.event.level);
            }
        });
        return Array.from(levels).sort();
    }, [runLogs.logs]);

    // Filter logs based on clicked node, search query, and level filters
    const filteredLogs = useMemo(() => {
        return runLogs.logs.filter((log) => {
            // Filter by clicked node
            if (clickedNode !== null && log.step_key !== clickedNode.id) {
                return false;
            }

            // Filter by search query
            if (searchQuery) {
                const query = searchQuery.toLowerCase();
                const searchableText = [
                    log.event.message,
                    log.step_key,
                    log.source,
                    log.event.log_type,
                    log.event.level
                ].join(' ').toLowerCase();
                
                if (!searchableText.includes(query)) {
                    return false;
                }
            }

            // Filter by selected levels
            if (selectedLevels.size > 0 && !selectedLevels.has(log.event.level)) {
                return false;
            }

            return true;
        });
    }, [runLogs.logs, clickedNode, searchQuery, selectedLevels]);

    const toggleLevel = (level: LogLevel) => {
        const newSelectedLevels = new Set(selectedLevels);
        if (newSelectedLevels.has(level)) {
            newSelectedLevels.delete(level);
        } else {
            newSelectedLevels.add(level);
        }
        setSelectedLevels(newSelectedLevels);
    };

    const clearFilters = () => {
        setSearchQuery("");
        setSelectedLevels(new Set());
    };

    const hasActiveFilters = searchQuery || selectedLevels.size > 0;

    return (
        <div className="flex flex-col h-full">
            {/* Toolbar */}
            <div className="bg-white border-b border-gray-200 px-4 py-3">
                <div className="flex items-center gap-3">
                    {/* Search */}
                    <div className="relative flex-1 max-w-md">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search logs..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery("")}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                            >
                                <X size={14} className="text-gray-400" />
                            </button>
                        )}
                    </div>

                    {/* Filter toggle */}
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={`
                            flex items-center gap-2 px-3 py-2 border rounded-lg text-sm transition-colors
                            ${showFilters || hasActiveFilters
                                ? 'border-blue-500 bg-blue-50 text-blue-700'
                                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                            }
                        `}
                    >
                        <Filter size={16} />
                        Filters
                        {selectedLevels.size > 0 && (
                            <span className="bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                                {selectedLevels.size}
                            </span>
                        )}
                    </button>

                    {/* Clear filters */}
                    {hasActiveFilters && (
                        <button
                            onClick={clearFilters}
                            className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700"
                        >
                            Clear all
                        </button>
                    )}

                    {/* Results count */}
                    <div className="text-sm text-gray-500">
                        {filteredLogs.length} of {runLogs.logs.length} logs
                    </div>
                </div>

                {/* Filter pills */}
                {showFilters && (
                    <div className="mt-3 flex flex-wrap gap-2">
                        {availableLevels.map((level) => {
                            const isSelected = selectedLevels.has(level);
                            return (
                                <button
                                    key={level}
                                    onClick={() => toggleLevel(level)}
                                    className={`
                                        flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors
                                        ${isSelected
                                            ? getLevelStyles(level).selectedBg + ' ' + getLevelStyles(level).selectedText
                                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }
                                    `}
                                >
                                    {getLevelIcon(level)}
                                    {level}
                                </button>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Table */}
            <div className="flex-1 overflow-auto">
                <table className={`${tableClass} divide-y divide-gray-200`}>
                    {enableResponsiveColumns ? (
                        <colgroup>
                            <col className="w-[15%] min-w-[140px]" />
                            <col className="w-[15%] min-w-[120px]" />
                            <col className="w-[10%] min-w-[80px]" />
                            <col className="w-[45%] min-w-[300px]" />
                            <col className="w-[15%] min-w-[100px]" />
                        </colgroup>
                    ) : (
                        <colgroup>
                            <col style={{ width: "20%" }} />
                            <col style={{ width: "15%" }} />
                            <col style={{ width: "10%" }} />
                            <col style={{ width: "40%" }} />
                            <col style={{ width: "15%" }} />
                        </colgroup>
                    )}
                    <thead className="bg-gray-50 sticky top-0">
                        <tr>
                            <TableHeader>Timestamp</TableHeader>
                            <TableHeader>Step Key</TableHeader>
                            <TableHeader>Source</TableHeader>
                            <TableHeader>Message</TableHeader>
                            <TableHeader>Level</TableHeader>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                        {filteredLogs.length > 0 ? (
                            filteredLogs.map((log, index) => (
                                <LogRow key={index} log={log} />
                            ))
                        ) : (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                    {hasActiveFilters ? (
                                        <div>
                                            <Search size={48} className="mx-auto mb-4 text-gray-300" />
                                            <p className="text-lg font-medium mb-2">No logs found</p>
                                            <p>Try adjusting your search or filters</p>
                                        </div>
                                    ) : (
                                        <div>
                                            <Info size={48} className="mx-auto mb-4 text-gray-300" />
                                            <p className="text-lg font-medium mb-2">No logs available</p>
                                            <p>Logs will appear here once the workflow runs</p>
                                        </div>
                                    )}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// Helper Components
function TableHeader({ children }: { children: React.ReactNode }) {
    return (
        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">
            {children}
        </th>
    );
}

function LogRow({ log }: { log: any }) {
    const levelStyles = getLevelStyles(log.event.level);
    
    return (
        <tr className={`hover:bg-gray-50 ${levelStyles.rowBg}`}>
            <td className="px-4 py-3 text-sm text-gray-900">
                <div className="font-mono text-xs">
                    {formatTimestamp(log.timestamp)}
                </div>
            </td>
            <td className="px-4 py-3 text-sm">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    {log.step_key || "N/A"}
                </span>
            </td>
            <td className="px-4 py-3 text-sm text-gray-600">
                {log.source}
            </td>
            <td className="px-4 py-3 text-sm text-gray-900">
                <div className="max-w-md">
                    {log.event.message}
                </div>
            </td>
            <td className="px-4 py-3">
                <span className={`
                    inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium
                    ${levelStyles.bg} ${levelStyles.text}
                `}>
                    {getLevelIcon(log.event.level)}
                    {log.event.level}
                </span>
            </td>
        </tr>
    );
}

// Utility Functions
function getLevelIcon(level: LogLevel, size: number = 12) {
    switch (level?.toLowerCase()) {
        case 'error':
            return <AlertCircle size={size} />;
        case 'warning':
        case 'warn':
            return <AlertTriangle size={size} />;
        case 'debug':
            return <Bug size={size} />;
        case 'info':
        default:
            return <Info size={size} />;
    }
}

function getLevelStyles(level: LogLevel) {
    switch (level?.toLowerCase()) {
        case 'error':
            return {
                bg: 'bg-red-100',
                text: 'text-red-800',
                selectedBg: 'bg-red-500',
                selectedText: 'text-white',
                rowBg: 'hover:bg-red-50'
            };
        case 'warning':
        case 'warn':
            return {
                bg: 'bg-yellow-100',
                text: 'text-yellow-800',
                selectedBg: 'bg-yellow-500',
                selectedText: 'text-white',
                rowBg: 'hover:bg-yellow-50'
            };
        case 'debug':
            return {
                bg: 'bg-purple-100',
                text: 'text-purple-800',
                selectedBg: 'bg-purple-500',
                selectedText: 'text-white',
                rowBg: 'hover:bg-purple-50'
            };
        case 'info':
        default:
            return {
                bg: 'bg-blue-100',
                text: 'text-blue-800',
                selectedBg: 'bg-blue-500',
                selectedText: 'text-white',
                rowBg: 'hover:bg-blue-50'
            };
    }
}

function formatTimestamp(timestamp: any): string {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString(undefined, {
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    } catch (error) {
        return timestamp?.toString() || "N/A";
    }
}
