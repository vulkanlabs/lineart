"use client";

import React, { useState } from "react";
import { useUser } from "@stackframe/stack";

import WorkflowFrame from "@/components/workflow/frame";
import WorkflowSidebar from "@/components/workflow/sidebar";
import { fetchComponentVersion } from "@/lib/api";

export default function Page({ params }) {
    const [clickedNode, setClickedNode] = useState([]);
    const user = useUser();

    async function loadData(componentId: string, componentVersionId: string) {
        const data = await fetchComponentVersion(user, componentId, componentVersionId).then(
            (data) => {
                return JSON.parse(data.node_definitions);
            },
        );
        // TODO: temporary fix to add input node (ComponentDefinition doesn't have
        // an internally inserted input node).
        data["input_node"] = {
            name: "input_node",
            node_type: "INPUT",
            hidden: false,
            description: "Input node",
            dependencies: null,
            metadata: {},
        };
        return data;
    }

    return (
        <div className="w-full h-full grid grid-cols-12">
            <div className="col-span-8">
                <div className="w-full h-full">
                    <WorkflowFrame
                        dataLoader={() =>
                            loadData(params.component_id, params.component_version_id)
                        }
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
