"use client";
import React, { useState } from "react";
import type { EdgeLayoutConfig, NodeLayoutConfig } from "../../lib/workflow/types";
import type { RunData, RunLogs, StepMetadataBase } from "@vulkanlabs/client-open";

export interface RunPageContentConfig {
    // Component dependencies injected by apps
    WorkflowFrame: React.ComponentType<{
        nodes: any[];
        edges: EdgeLayoutConfig[];
        onNodeClick: (event: any, node: any) => void;
        onPaneClick: () => void;
    }>;
    RunNodeLayout: any;
    
    // Style configuration differences
    containerOverflow?: "hidden" | "scroll";
    sidebarOverflow?: "hidden" | "auto";
    tableClass?: "w-full" | "min-w-full";
    useResponsiveColumns?: boolean; // true for OSS, false for SaaS
}

export function SharedRunPageContent({
    nodes,
    edges,
    runLogs,
    runData,
    config,
}: {
    nodes: any[];
    edges: EdgeLayoutConfig[];
    runLogs: RunLogs;
    runData: RunData;
    config: RunPageContentConfig;
}) {
    const [clickedNode, setClickedNode] = useState(null);
    const {
        WorkflowFrame,
        containerOverflow = "hidden",
        sidebarOverflow = "hidden", 
        tableClass = "w-full",
        useResponsiveColumns = true
    } = config;

    return (
        <div className={`grid grid-rows-2 h-full w-full overflow-${containerOverflow}`}>
            <div className="row-span-1 w-full border-b-2">
                <div className="w-full h-full grid grid-cols-12">
                    <div className="col-span-8">
                        <div className="w-full h-full">
                            <WorkflowFrame
                                nodes={nodes}
                                edges={edges}
                                onNodeClick={(_, node) => setClickedNode(node)}
                                onPaneClick={() => setClickedNode(null)}
                            />
                        </div>
                    </div>
                    <div className={`col-span-4 border-l-2 overflow-${sidebarOverflow}`}>
                        <WorkflowSidebar clickedNode={clickedNode} runData={runData} />
                    </div>
                </div>
            </div>
            <div className="row-span-1 w-full">
                <LogsTable 
                    runLogs={runLogs} 
                    clickedNode={clickedNode} 
                    tableClass={tableClass}
                    useResponsiveColumns={useResponsiveColumns}
                />
            </div>
        </div>
    );
}

function LogsTable({
    runLogs,
    clickedNode,
    tableClass = "w-full",
    useResponsiveColumns = true
}: {
    runLogs: RunLogs;
    clickedNode: NodeLayoutConfig | null;
    tableClass?: "w-full" | "min-w-full";
    useResponsiveColumns?: boolean;
}) {
    const filteredLogs = runLogs.logs.filter(
        (log) => clickedNode === null || log.step_key === clickedNode.id,
    );

    const responsiveColumns = (
        <colgroup>
            <col className="w-[12%] min-w-[100px]" />
            <col className="w-[18%] min-w-[120px]" />
            <col className="w-[8%] min-w-[80px]" />
            <col className="w-[12%] min-w-[100px]" />
            <col className="w-[40%] min-w-[200px]" />
            <col className="w-[10%] min-w-[80px]" />
        </colgroup>
    );

    const fixedColumns = (
        <colgroup>
            <col style={{ width: "15%" }} />
            <col style={{ width: "20%" }} />
            <col style={{ width: "10%" }} />
            <col style={{ width: "15%" }} />
            <col style={{ width: "30%" }} />
            <col style={{ width: "10%" }} />
        </colgroup>
    );

    return (
        <div className="flex flex-row w-full h-full overflow-y-auto">
            <table className={`${tableClass} divide-y divide-gray-200 border-collapse`}>
                {useResponsiveColumns ? responsiveColumns : fixedColumns}
                <thead className="bg-gray-50 sticky top-0">
                    <tr>
                        <TableHeader>Timestamp</TableHeader>
                        <TableHeader>Step Key</TableHeader>
                        <TableHeader>Source</TableHeader>
                        <TableHeader>Log Type</TableHeader>
                        <TableHeader>Message</TableHeader>
                        <TableHeader>Level</TableHeader>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {filteredLogs.map((log, index) => (
                        <tr key={index}>
                            <TableCell>
                                {(() => {
                                    try {
                                        return new Date(log.timestamp).toLocaleString();
                                    } catch (error) {
                                        return log.timestamp?.toString() || "N/A";
                                    }
                                })()}
                            </TableCell>
                            <TableCell>{log.step_key || "N/A"}</TableCell>
                            <TableCell>{log.source}</TableCell>
                            <TableCell>{log.event.log_type || "N/A"}</TableCell>
                            <TableCell>{log.event.message}</TableCell>
                            <TableCell>{log.event.level}</TableCell>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function TableHeader({ children }: { children: React.ReactNode }) {
    return (
        <th className="xl:text-xs xl:px-4 xl:py-2 2xl:px-6 2xl:py-4 2xl:text-sm text-left border-r-2 font-medium text-gray-500 uppercase tracking-wider sticky top-0">
            {children}
        </th>
    );
}

function TableCell({ children }: { children: React.ReactNode }) {
    return (
        <td className="xl:text-xs xl:px-4 xl:py-2 2xl:px-6 2xl:py-4 2xl:text-sm border-r-2 whitespace-normal text-gray-500">
            {children}
        </td>
    );
}

function WorkflowSidebar({
    clickedNode,
    runData,
}: {
    clickedNode: any | null;
    runData: RunData;
}) {
    return (
        <div className="h-full bg-white border-l-2 overflow-auto">
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
        <div className="flex flex-col px-5">
            <div>
                <h1 className="mt-5 text-lg font-semibold">Run ID:</h1>
                <pre className="text-lg font-light">{runData.run_id}</pre>
            </div>
            <div>
                <h1 className="mt-5 text-lg font-semibold">Last Updated:</h1>
                <pre className="text-lg font-light">
                    {(() => {
                        try {
                            return runData.last_updated_at
                                ? new Date(runData.last_updated_at).toLocaleString()
                                : "N/A";
                        } catch (error) {
                            return runData.last_updated_at?.toString() || "N/A";
                        }
                    })()}
                </pre>
            </div>
        </div>
    );
}

function NodeContent({ clickedNode }: { clickedNode: any | null }) {
    if (clickedNode === null) {
        return (
            <div className="flex flex-col px-5">
                <h1 className="mt-5 text-lg font-semibold">No node selected</h1>
            </div>
        );
    }

    const content = [
        {
            name: "Name",
            value: clickedNode.data.label,
        },
        {
            name: "Type",
            value: clickedNode.data.type,
        },
        {
            name: "Duration",
            value: clickedNode.data.run?.metadata
                ? getRunDuration(clickedNode.data.run.metadata)
                : "",
        },
    ];

    return (
        <div className="flex flex-col p-5 gap-4 overflow-auto">
            <h1 className="text-lg font-semibold">Node details</h1>
            <div className="flex flex-row gap-12">
                <div>
                    {content.map(({ name }) => (
                        <div className="py-1 text-lg font-normal" key={name}>
                            {name}
                        </div>
                    ))}
                </div>
                <div>
                    {content.map(({ name, value }) => (
                        <div className="py-1 text-lg font-light" key={`${name}-value`}>
                            {value}
                        </div>
                    ))}
                </div>
            </div>
            <h1 className="text-lg font-semibold">Output</h1>
            <div className="bg-slate-100 rounded overflow-auto">
                <pre className="p-5 text-xs">
                    {JSON.stringify(clickedNode.data.run?.output, null, 2)}
                </pre>
            </div>
        </div>
    );
}

function getRunDuration(run: StepMetadataBase): string {
    const start = new Date(run.start_time * 1000);
    const end = new Date(run.end_time * 1000);
    return formatDistance(end.getTime() - start.getTime());
}

function formatDistance(duration: number): string {
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