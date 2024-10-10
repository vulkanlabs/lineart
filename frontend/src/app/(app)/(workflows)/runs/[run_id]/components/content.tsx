"use client";
import React, { useState } from "react";

import { WorkflowFrame, NodeLayoutConfig } from "./frame";
import type {
    NodeDependency,
    NodeDefinition,
    GraphDefinition,
    RunStepMetadata,
    RunStep,
    RunSteps,
    RunData,
    RunNode,
    RunLogEvent,
    RunLog,
    RunLogs,
} from "../types";

export default function RunPageContent({
    runGraph,
    runLogs,
}: {
    runGraph: RunNode[];
    runLogs: RunLogs;
}) {
    const [clickedNode, setClickedNode] = useState(null);

    return (
        <div className="grid grid-rows-2 h-full w-full overflow-scroll">
            <div className="row-span-1 w-full border-b-2">
                <div className="w-full h-full grid grid-cols-12">
                    <div className="col-span-8">
                        <div className="w-full h-full">
                            <WorkflowFrame
                                runGraph={runGraph}
                                onNodeClick={(_, node) => setClickedNode(node)}
                                onPaneClick={() => setClickedNode(null)}
                            />
                        </div>
                    </div>
                    <div className="col-span-4 border-l-2">
                        <WorkflowSidebar clickedNode={clickedNode} />
                    </div>
                </div>
            </div>
            <div className="row-span-1 w-full">
                <LogsTable runLogs={runLogs} clickedNode={clickedNode} />
            </div>
        </div>
    );
}

function LogsTable({
    runLogs,
    clickedNode,
}: {
    runLogs: RunLogs;
    clickedNode: NodeLayoutConfig | null;
}) {
    const filteredLogs = runLogs.logs.filter(
        (log) => clickedNode === null || log.step_key === clickedNode.id
    );

    return (
        <div className="flex flex-row w-full h-full overflow-scroll">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
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
                            <TableCell>{log.timestamp}</TableCell>
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

function TableHeader({ children }) {
    return (
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            {children}
        </th>
    );
}

function TableCell({ children }) {
    return <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">{children}</td>;
}

function WorkflowSidebar({ clickedNode }: { clickedNode: NodeLayoutConfig | null }) {
    return (
        <div className="h-full bg-white border-l-2">
            <NodeContent clickedNode={clickedNode} />
        </div>
    );
}

function NodeParam({ name, value }) {
    return (
        <div className="grid grid-cols-4 my-2">
            <div className="col-span-2 text-lg font-normal">{name}</div>
            <div className="col-span-2 overflow-scroll">{value}</div>
        </div>
    );
}

function NodeContent({ clickedNode }: { clickedNode: NodeLayoutConfig | null }) {
    if (clickedNode === null) {
        return (
            <div className="flex flex-col px-5">
                <h1 className="mt-5 text-lg font-semibold">No node selected</h1>
            </div>
        );
    }

    return (
        <div className="flex flex-col px-5">
            <div className="mt-5">
                <NodeParam name={"Name"} value={clickedNode.data.label} />
                <NodeParam name={"Type"} value={clickedNode.data.type} />
                <NodeParam
                    name={"Duration"}
                    value={
                        clickedNode.data?.run?.metadata
                            ? getRunDuration(clickedNode.data.run.metadata)
                            : ""
                    }
                />
                <NodeParam
                    name={"Output"}
                    value={clickedNode.data?.run ? JSON.stringify(clickedNode.data.run.output) : ""}
                />
            </div>
        </div>
    );
}

function getRunDuration(run: RunStepMetadata): string {
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
