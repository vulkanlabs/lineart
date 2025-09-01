"use client";

import React, { useState } from "react";

import type {
    NodeDefinitionDict,
    PolicyVersion,
    RunData,
    RunLogs,
    StepMetadataBase,
} from "@vulkanlabs/client-open";

import { WorkflowFrame } from "./workflow/frame";
import { EdgeLayoutConfig, NodeLayoutConfig, RunNodeLayout } from "./workflow/types";
import { makeGraphElements } from "./workflow/graph";



export function LogsTable({
    runLogs,
    clickedNode,
    tableClass = "w-full",
    enableResponsiveColumns = true,
}: {
    runLogs: RunLogs;
    clickedNode: NodeLayoutConfig | null;
    tableClass?: "w-full" | "min-w-full";
    enableResponsiveColumns?: boolean;
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
                {enableResponsiveColumns ? responsiveColumns : fixedColumns}
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