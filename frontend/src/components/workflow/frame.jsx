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
import { makeWorkflow } from "@/lib/workflow/workflow";

function filterHiddenEdges(edges, state) {
    return edges.filter((edge) => {
        const fromOpenComponent = edge.isComponentIO && state[edge.source]?.isOpen;
        const toOpenComponent = edge.isComponentIO && state[edge.target]?.isOpen;

        const fromClosedComponentChild =
            edge.fromComponentChild && !state[edge.fromComponent]?.isOpen;
        const toClosedComponentChild = edge.toComponentChild && !state[edge.toComponent]?.isOpen;
        return !(
            fromOpenComponent ||
            toOpenComponent ||
            toClosedComponentChild ||
            fromClosedComponentChild
        );
    });
}

function VulkanWorkflow({ graphData, onNodeClick, onPaneClick }) {
    const [componentsState, setComponentsState] = useState([]);
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const loadAndLayout = () => {
        const components = Object.values(graphData).filter(
            (node) => node.node_type === "COMPONENT",
        );
        const states = components.map((c) => ({ [c.name]: { isOpen: false } }));
        const componentsState = Object.assign({}, ...states);
        setComponentsState(componentsState);

        makeWorkflow(graphData, componentsState).then(([layoutedNodes, layoutedEdges]) => {
            const filteredEdges = filterHiddenEdges(layoutedEdges, componentsState);
            setNodes(layoutedNodes);
            setEdges(filteredEdges);
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

            makeWorkflow(graphData, newComponentsState).then(([layoutedNodes, layoutedEdges]) => {
                const filteredEdges = filterHiddenEdges(layoutedEdges, newComponentsState);
                setNodes(layoutedNodes);
                setEdges(filteredEdges);
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
