"use client";

import React, { useState } from "react";

import WorkflowFrame from "@/components/workflow/frame";
import WorkflowSidebar, { type VulkanNode } from "@/components/workflow/sidebar";

export default function WorkflowPage({ graphData }) {
    const [clickedNode, setClickedNode] = useState<VulkanNode>(null);

    return (
        <div className="w-full h-full grid grid-cols-12">
            <div className="col-span-8">
                <div className="w-full h-full">
                    <WorkflowFrame
                        graphData={graphData}
                        onNodeClick={(_: any, node: VulkanNode) => setClickedNode(node)}
                        onPaneClick={() => setClickedNode(null)}
                    />
                </div>
            </div>
            <div className="col-span-4">
                <WorkflowSidebar clickedNode={clickedNode} />
            </div>
        </div>
    );
}
