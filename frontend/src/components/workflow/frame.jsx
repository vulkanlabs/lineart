"use client";

import React, { useState, useLayoutEffect, useCallback } from "react";
import {
    ReactFlow,
    ReactFlowProvider,
    MiniMap,
    Controls,
    ConnectionLineType,
    Background,
    BackgroundVariant,
    useNodesState,
    useEdgesState,
    useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { nodeTypes } from "@/components/workflow/nodes";
import layoutGraph from "@/lib/workflow";

function VulkanWorkflow({ graphData, onNodeClick, onPaneClick }) {
    const [componentsState, setComponentsState] = useState([]);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const loadAndLayout = () => {
        const components = Object.values(graphData).filter((node) => node.node_type === "COMPONENT");
        const states = components.map((c) => ({ [c.name]: { isOpen: false } }));
        const componentsState = Object.assign({}, ...states);
        setComponentsState(componentsState);

        layoutGraph(graphData, componentsState).then(([layoutedNodes, layoutedEdges]) => {
            setNodes(layoutedNodes);
            setEdges(layoutedEdges);
            window.requestAnimationFrame(() => fitView());
        });
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

    const clickNode = (e, node) => {
        resetClick();

        if (node.data.type === "COMPONENT") {
            const newComponentsState = { ...componentsState };
            newComponentsState[node.id].isOpen = !newComponentsState[node.id].isOpen;
            setComponentsState(newComponentsState);

            layoutGraph(graphData, newComponentsState).then(([layoutedNodes, layoutedEdges]) => {
                setNodes(layoutedNodes);
                setEdges(layoutedEdges);
            });
            onNodeClick(e, []);
            return;
        }

        const newNodes = nodes.map((n) => {
            if (n.id === node.id) {
                n.data.clicked = true;
            }
            return n;
        });
        setNodes(newNodes);
        onNodeClick(e, node);
    };

    const clickPane = (e) => {
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
            fitViewOptions={{ maxZoom: 1 }}
            fitView
        >
            <Background color="#ccc" variant={BackgroundVariant.Dots} />
            <MiniMap nodeStrokeWidth={3} zoomable pannable />
            <Controls />
        </ReactFlow>
    );
}

export default function WorkflowFrame({ graphData, onNodeClick, onPaneClick }) {
    return (
        <ReactFlowProvider>
            <VulkanWorkflow
                graphData={graphData}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
            />
        </ReactFlowProvider>
    );
}
