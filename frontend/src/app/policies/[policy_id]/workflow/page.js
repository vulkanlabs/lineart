"use client";

import React, { useState } from "react";

import Workflow from "./workflow";
import WorkflowSidebar from "@/components/workflow/workflow-sidebar";


export default function Page({ params }) {
    const [clickedNode, setClickedNode] = useState([]);

    return (
        <div className="w-full h-full grid grid-cols-12">
            <div className="col-span-8">
                <div className='w-full h-full'>
                    <Workflow
                        policyId={params.policy_id}
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