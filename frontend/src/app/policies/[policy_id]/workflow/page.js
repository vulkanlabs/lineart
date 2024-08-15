"use client";

import React, { useState } from "react";

import Workflow from "./workflow";
import WorkflowSidebar from "@/components/workflow-sidebar";


export default function Page({ params }) {
    const [showSidebar, setShowSidebar] = useState(false);
    const [clickedNode, setClickedNode] = useState([]);

    function openNodeSidebar(node) {
        console.log("Clicked node:", node);
        setClickedNode(node);
        setShowSidebar(true);
    }

    if (!showSidebar) {
        return (
            <div className='w-full max-w-full h-full'>
                <Workflow policyId={params.policy_id} onNodeClick={(_, node) => openNodeSidebar(node)} />
            </div>
        );
    }

    return (
        <div className="w-full h-full grid grid-cols-6">
            <div className="col-span-4">
                <div className='w-full h-full'>
                <Workflow policyId={params.policy_id} onNodeClick={(_, node) => openNodeSidebar(node)} />
                </div>
            </div>
            <div className="col-span-2">
                <WorkflowSidebar clickedNode={clickedNode} closeFunc={() => setShowSidebar(false)} />
            </div>
        </div>
    );
}