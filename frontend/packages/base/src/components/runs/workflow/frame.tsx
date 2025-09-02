"use client";

import React, { useLayoutEffect, useCallback } from "react";
import {
    ReactFlow,
    ReactFlowProvider,
    Controls,
    ConnectionLineType,
    Background,
    BackgroundVariant,
    useNodesState,
    useEdgesState,
    useReactFlow,
} from "@xyflow/react";

import { nodeTypes } from "./nodes";
import { defaultElkOptions } from "./options";
import type { RunNodeLayout, EdgeLayoutConfig, LayoutedNode } from "./types";
import { layoutGraph } from "./graph";
import { EmptyWorkflow } from "../loading-states";

function VulkanWorkflow({
    graphNodes,
    graphEdges,
    onNodeClick,
    onPaneClick,
}: {
    graphNodes: RunNodeLayout[];
    graphEdges: EdgeLayoutConfig[];
    onNodeClick: any;
    onPaneClick: any;
}) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const loadAndLayout = () => {
        layoutGraph(graphNodes, graphEdges, defaultElkOptions).then(
            ([layoutedNodes, layoutedEdges]) => {
                setNodes(layoutedNodes);
                setEdges(layoutedEdges);
                window.requestAnimationFrame(() => fitView());
            },
        );
    };

    const onLayout = useCallback(loadAndLayout, []);

    // Calculate the initial layout on mount.
    useLayoutEffect(() => {
        onLayout();
    }, []);

    const resetClick = () => {
        const newNodes = nodes.map((n) => {
            n.data.clicked = false;
            return n;
        });
        setNodes(newNodes);
    };

    const clickNode = (e: React.MouseEvent, node: LayoutedNode) => {
        resetClick();
        const newNodes = nodes.map((n) => {
            if (n.id === node.id) {
                n.data.clicked = true;
            }
            return n;
        });
        setNodes(newNodes);
        onNodeClick(e, node);
    };

    const clickPane = (e: React.MouseEvent) => {
        resetClick();
        onPaneClick(e);
    };

    return (
        <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={clickNode}
            onPaneClick={clickPane}
            nodeTypes={nodeTypes}
            connectionLineType={ConnectionLineType.SmoothStep}
            defaultEdgeOptions={{
                style: { stroke: "#6b7280", strokeWidth: 2 },
                type: "smoothstep",
            }}
            minZoom={0.1}
            maxZoom={2}
            fitViewOptions={{ maxZoom: 1 }}
            fitView
            proOptions={{ hideAttribution: true }}
        >
            <Background color="#e5e7eb" size={2} gap={20} variant={BackgroundVariant.Dots} />
            <Controls showInteractive={false} orientation="horizontal" />
        </ReactFlow>
    );
}

export function WorkflowFrame({ nodes, edges, onNodeClick, onPaneClick }) {
    // Show empty state if no nodes
    if (!nodes || nodes.length === 0) {
        return <EmptyWorkflow />;
    }

    return (
        <ReactFlowProvider>
            <VulkanWorkflow
                graphNodes={nodes}
                graphEdges={edges}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
            />
        </ReactFlowProvider>
    );
}
