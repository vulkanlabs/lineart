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
            minZoom={0.1}
            maxZoom={2}
            fitViewOptions={{ maxZoom: 1 }}
            fitView
            proOptions={{ hideAttribution: true }}
        >
            <Background
                    color="#c8c8c8"
                    size={3}
                    gap={30}
                    variant={BackgroundVariant.Dots}
                />
            <Controls
                showInteractive={false}
                orientation="horizontal"
            />
        </ReactFlow>
    );
}

export function WorkflowFrame({ nodes, edges, onNodeClick, onPaneClick }) {
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
