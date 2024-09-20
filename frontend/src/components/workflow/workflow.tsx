"use client";

import React, { useState } from "react";

import WorkflowFrame from "@/components/workflow/frame";
import WorkflowSidebar from "@/components/workflow/sidebar";

export default function WorkflowPage({ graphData }) {
    const [clickedNode, setClickedNode] = useState([]);

    return (
        <div className="w-full h-full grid grid-cols-12">
            <div className="col-span-8">
                <div className="w-full h-full">
                    <WorkflowFrame
                        graphData={graphData}
                        onNodeClick={(_, node) => setClickedNode(node)}
                        onPaneClick={() => setClickedNode([])}
                    />
                </div>
            </div>
            <div className="col-span-4">
                <WorkflowSidebar clickedNode={clickedNode} />
            </div>
        </div>
    );
}
