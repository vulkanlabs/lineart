"use client";

import React, { useState } from "react";
import {
    ReactFlow,
    MiniMap,
    Controls,
    ConnectionLineType,
    Background,
    BackgroundVariant
} from '@xyflow/react';

import dagre from '@dagrejs/dagre';

import '@xyflow/react/dist/style.css';

import WorkflowSidebar from "@/components/workflow-sidebar";


export default function Page({ params }) {
    const [showSidebar, setShowSidebar] = useState(false);
    const [clickedNode, setClickedNode] = useState([]);
    const [nodes, setNodes] = useState([]);
    const [edges, setEdges] = useState([]);
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));

    const initGraph = () => {
        assembleGraph(params.policy_id, dagreGraph)
            .then(([layoutedNodes, layoutedEdges]) => {
                console.log("nodes:", layoutedNodes);
                console.log("edges:", layoutedEdges);

                setNodes(layoutedNodes);
                setEdges(layoutedEdges);
            });
    };

    function openNodeSidebar(node) {
        console.log("Clicked node:", node);
        setClickedNode(node);
        setShowSidebar(true);
    }

    if (!showSidebar) {
        return (
            <div className='w-full max-w-full h-full'>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onInit={initGraph}
                    onNodeClick={(_, node) => openNodeSidebar(node)}
                    connectionLineType={ConnectionLineType.SmoothStep}
                    fitView
                >
                    <Background color="#ccc" variant={BackgroundVariant.Dots} />
                    <MiniMap nodeStrokeWidth={3} zoomable pannable />
                    <Controls />
                </ReactFlow>
            </div>
        );
    }

    return (
        <div className="w-full h-full grid grid-cols-6">
            <div className="col-span-4">
                <div className='w-full h-full'>
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onInit={initGraph}
                        onNodeClick={(_, node) => openNodeSidebar(node)}
                        connectionLineType={ConnectionLineType.SmoothStep}
                        fitView
                    >
                        <Background color="#ccc" variant={BackgroundVariant.Dots} />
                        <MiniMap nodeStrokeWidth={3} zoomable pannable />
                        <Controls />
                    </ReactFlow>
                </div>
            </div>
            <div className="col-span-2">
                <WorkflowSidebar clickedNode={clickedNode} closeFunc={() => setShowSidebar(false)} />
            </div>
        </div>
    );
}

async function assembleGraph(policyId, graph) {
    const graphData = await getGraphData(policyId)
        .then((policyVersionData) => {
            return JSON.parse(policyVersionData.graph_definition);
        });

    const vulkanNodes = Object.entries(graphData).map(([name, node]) => {
        let nodeData = {
            id: name,
            data: {
                label: name,
                description: node.description,
                type: node.node_type,
            }
        };
        if (node.metadata !== null) {
            Object.entries(node.metadata).map(([key, value]) => {
                nodeData.data[key] = value;
            })
        }
        return nodeData;
    });

    const vulkanEdges = Object.entries(graphData).flatMap(([name, node]) => {
        if (node.dependencies === null) {
            return [];
        }

        return node.dependencies.map((dep) => {
            // TODO: If `dep` is an array, it means that it comes from
            // a specific output of a node. For now, we discard it, as
            // we don't display the node outputs.
            if (Array.isArray(dep)) {
                dep = dep[0];
            }

            return {
                id: `${dep}-${name}`,
                source: dep,
                target: name,
            };
        });
    });

    const [layoutedNodes, layoutedEdges] = getLayoutedElements(
        graph, vulkanNodes, vulkanEdges);

    return [layoutedNodes, layoutedEdges];
}


function getLayoutedElements(graph, nodes, edges) {
    const nodeWidth = 172;
    const nodeHeight = 36;
    const direction = "TB";

    graph.setGraph({ rankdir: direction });

    nodes.forEach((node) => {
        graph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
    });

    edges.forEach((edge) => {
        graph.setEdge(edge.source, edge.target);
    });

    dagre.layout(graph);

    const newNodes = nodes.map((node) => {
        const nodeWithPosition = graph.node(node.id);
        const newNode = {
            ...node,
            targetPosition: 'top',
            sourcePosition: 'bottom',
            // We are shifting the dagre node position (anchor=center center) to the top left
            // so it matches the React Flow node anchor point (top left).
            position: {
                x: nodeWithPosition.x - nodeWidth / 2,
                y: nodeWithPosition.y - nodeHeight / 2,
            },
        };

        return newNode;
    });

    return [newNodes, edges];
};


async function getGraphData(policyId) {
    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const policyUrl = new URL(`/policies/${policyId}`, baseUrl);
    const policyVersionId = await fetch(policyUrl)
        .then((res) => res.json())
        .catch((error) => {
            throw new Error("Failed to fetch policy version id for policy",
                { cause: error });
        })
        .then((response) => {
            if (response.active_policy_version_id === null) {
                throw new Error(`Policy ${policyId} has no active version`);
            }
            return response.active_policy_version_id;
        });


    if (policyVersionId === null) {
        throw new Error(`Policy ${policyId} has no active version`);
    }

    const versionUrl = new URL(`/policyVersions/${policyVersionId}`, baseUrl);
    const data = await fetch(versionUrl)
        .then((res) => res.json())
        .catch((error) => {
            throw new Error("Failed to fetch graph data", { cause: error });
        });
    return data;
}