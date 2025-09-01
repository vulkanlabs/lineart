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

import { LogsTable } from "./run-logs";

export interface RunPageConfig {
    containerOverflow?: "hidden" | "scroll";
    sidebarOverflow?: "hidden" | "auto";
    tableClass?: "w-full" | "min-w-full";
    enableResponsiveColumns?: boolean;
}

export function RunPageContent({
    nodes,
    runLogs,
    runData,
    config,
}: {
    nodes: NodeDefinitionDict[];
    runLogs: RunLogs;
    runData: RunData;
    config?: RunPageConfig;
}) {
    const [clickedNode, setClickedNode] = useState(null);
    const {
        containerOverflow = "scroll",
        sidebarOverflow = "auto",
        tableClass = "w-full",
        enableResponsiveColumns = true,
    } = config || {};

    const containerOverflowClass =
        containerOverflow === "hidden" ? "overflow-hidden" : "overflow-scroll";
    const sidebarOverflowClass = sidebarOverflow === "hidden" ? "overflow-hidden" : "overflow-auto";

    const inputNode: NodeDefinitionDict = {
        name: "input_node",
        node_type: "INPUT",
        dependencies: null,
        metadata: null,
    };
    const allNodes = nodes.length > 0 ? [...nodes, inputNode] : nodes;

    const [nodesToLayout, edges] = makeGraphElements(allNodes);

    const runNodes: RunNodeLayout[] = nodesToLayout.map((node: NodeLayoutConfig) => {
        const runNode = {
            ...node,
            data: {
                ...node.data,
                run: runData.steps[node.id] || null,
            },
        };
        return runNode;
    });

    return (
        <div className={`grid grid-rows-2 h-full w-full ${containerOverflowClass}`}>
            <div className="row-span-1 w-full border-b-2">
                <div className="w-full h-full grid grid-cols-12">
                    <div className="col-span-8">
                        <div className="w-full h-full">
                            <WorkflowFrame
                                nodes={runNodes}
                                edges={edges}
                                onNodeClick={(_: any, node: any) => setClickedNode(node)}
                                onPaneClick={() => setClickedNode(null)}
                            />
                        </div>
                    </div>
                    <div className={`col-span-4 border-l-2 ${sidebarOverflowClass}`}>
                        <WorkflowSidebar clickedNode={clickedNode} runData={runData} />
                    </div>
                </div>
            </div>
            <div className="row-span-1 w-full">
                <LogsTable
                    runLogs={runLogs}
                    clickedNode={clickedNode}
                    tableClass={tableClass}
                    enableResponsiveColumns={enableResponsiveColumns}
                />
            </div>
        </div>
    );
}

function WorkflowSidebar({
    clickedNode,
    runData,
}: {
    clickedNode: RunNodeLayout | null;
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

function NodeContent({ clickedNode }: { clickedNode: RunNodeLayout | null }) {
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
