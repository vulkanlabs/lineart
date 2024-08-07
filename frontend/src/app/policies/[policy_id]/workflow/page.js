"use client";

import React, { useState } from "react";
import {
    ReactFlow,
    MiniMap,
    Controls,
    ConnectionLineType,
} from '@xyflow/react';

import dagre from '@dagrejs/dagre';

import '@xyflow/react/dist/style.css';


export default function Page({ params }) {
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

    return (
        <div className='w-full max-w-full h-full'>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onInit={initGraph}
                connectionLineType={ConnectionLineType.SmoothStep}
                fitView
            >
                <MiniMap nodeStrokeWidth={3} zoomable pannable />
                <Controls />
            </ReactFlow>
        </div>
    );
}


async function assembleGraph(policyId, graph) {
    const graphData = await getGraphData(policyId)
        .then((policyVersionData) => {
            return JSON.parse(policyVersionData.graph_definition);
        });

    const vulkanNodes = Object.entries(graphData).map(([name, node]) => {
        return {
            id: name,
            data: {
                label: name,
                description: node.description,
                type: node.node_type,
            }
        };
    });

    const vulkanEdges = Object.entries(graphData).flatMap(([name, node]) => {
        return node.dependencies.map((dep) => {
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

    const versionUrl = new URL(`/policies/${policyId}/versions/${policyVersionId}`, baseUrl);
    const data = await fetch(versionUrl)
        .then((res) => res.json())
        .catch((error) => {
            throw new Error("Failed to fetch graph data", { cause: error });
        });
    return data;
}