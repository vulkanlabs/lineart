"use client";

import React, { useState } from "react";

import WorkflowFrame from "@/components/workflow/frame";
import WorkflowSidebar from "@/components/workflow/sidebar";
import { fetchPolicyVersionData } from "@/lib/api";

export default function Page({ params }) {
    const [clickedNode, setClickedNode] = useState([]);

    async function loadData(policyId) {
        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        const data = await fetchPolicyVersionData(serverUrl, policyId).then((data) => {
            return JSON.parse(data.graph_definition);
        });
        return data;
    }

    return (
        <div className="w-full h-full grid grid-cols-12">
            <div className="col-span-8">
                <div className="w-full h-full">
                    <WorkflowFrame
                        dataLoader={() => loadData(params.policy_id)}
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
