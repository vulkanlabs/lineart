"use client";
import React, { useState } from "react";

import WorkflowFrame from "./frame";

export default function WorkflowPage({ graphData, runsData }) {
    const [clickedNode, setClickedNode] = useState([]);

    return (
        <div className="w-full h-full grid grid-cols-12">
            <div className="col-span-8">
                <div className="w-full h-full">
                    <WorkflowFrame
                        graphData={graphData}
                        runsData={runsData}
                        onNodeClick={(_, node) => setClickedNode(node)}
                        onPaneClick={() => setClickedNode([])}
                    />
                </div>
            </div>
            <div className="col-span-4 border-l-2">
                <WorkflowSidebar clickedNode={clickedNode} />
            </div>
        </div>
    );
}

function WorkflowSidebar({ clickedNode }) {
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

function NodeContent({ clickedNode }) {
    if (clickedNode.length === 0) {
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

type RunMetadata = {
    step_name: string;
    node_type: string;
    start_time: number;
    end_time: number;
    error?: string;
    extra?: any;
};

function getRunDuration(run: RunMetadata): string {
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
