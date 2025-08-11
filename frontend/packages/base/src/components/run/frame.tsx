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
import "@xyflow/react/dist/style.css";

import { nodeTypes } from "./nodes";
import { defaultElkOptions } from "./options";
import type { BaseRunNodeLayout } from "./types";

export interface RunFrameConfig {
    /** Function to layout the graph nodes and edges */
    layoutGraph: (nodes: any[], edges: any[], options: any) => Promise<[any[], any[]]>;
}

export interface RunFrameProps {
    nodes: BaseRunNodeLayout[];
    edges: any[]; // EdgeLayoutConfig - apps should provide their edge type
    onNodeClick: (e: React.MouseEvent, node: any) => void;
    onPaneClick: (e: React.MouseEvent) => void;
    config: RunFrameConfig;
}

function VulkanWorkflow({
    graphNodes,
    graphEdges,
    onNodeClick,
    onPaneClick,
    config,
}: {
    graphNodes: BaseRunNodeLayout[];
    graphEdges: any[];
    onNodeClick: any;
    onPaneClick: any;
    config: RunFrameConfig;
}) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const loadAndLayout = () => {
        const filteredNodes = graphNodes
            .filter((node) => node.data.type !== "COMPONENT")
            .map((n) => withRunNodeProps(n))
            .map((n) => {
                return {
                    ...n,
                    parentId: null,
                    parentReference: null,
                };
            });

        const filteredEdges = graphEdges.filter((edge) => {
            return !edge.isComponentIO || edge.fromComponentChild || edge.toComponentChild;
        });

        config.layoutGraph(filteredNodes, filteredEdges, defaultElkOptions).then(
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

    const clickNode = (e, node) => {
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
            minZoom={0.1}
            maxZoom={2}
            fitViewOptions={{ maxZoom: 1 }}
            fitView
        >
            <Background color="#ccc" variant={BackgroundVariant.Dots} />
            <Controls />
        </ReactFlow>
    );
}

export function WorkflowFrame({ nodes, edges, onNodeClick, onPaneClick, config }: RunFrameProps) {
    return (
        <ReactFlowProvider>
            <VulkanWorkflow
                graphNodes={nodes}
                graphEdges={edges}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                config={config}
            />
        </ReactFlowProvider>
    );
}

const NodeTypeToRunStepMapping = {
    TRANSFORM: "common",
    CONNECTION: "common",
    DATA_INPUT: "common",
    BRANCH: "common",
    DECISION: "common",
    COMPONENT: "common",
    POLICY: "common",
    TERMINATE: "terminate",
    INPUT: "entry",
};

function withRunNodeProps(node: BaseRunNodeLayout): BaseRunNodeLayout {
    if (Object.keys(NodeTypeToRunStepMapping).includes(node.data.type)) {
        node.type = NodeTypeToRunStepMapping[node.data.type];
    } else {
        // @ts-ignore - apps will provide proper typing
        node.targetPosition = "left";
        // @ts-ignore - apps will provide proper typing
        node.sourcePosition = "right";
    }

    return {
        ...node,
        draggable: false,
    };
}