"use client";
import ELK from "elkjs/lib/elk.bundled.js";
import React, { useState, useLayoutEffect, useCallback } from "react";
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

import type { NodeDependency, NodeDefinition, RunStep, RunNode } from "../types";
import { nodeTypes } from "./nodes";

function VulkanWorkflow({
    runGraph,
    onNodeClick,
    onPaneClick,
}: {
    runGraph: RunNode[];
    onNodeClick: any;
    onPaneClick: any;
}) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();

    const loadAndLayout = () => {
        layoutGraph(runGraph).then(([layoutedNodes, layoutedEdges]) => {
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

export function WorkflowFrame({ runGraph, onNodeClick, onPaneClick }) {
    return (
        <ReactFlowProvider>
            <VulkanWorkflow
                runGraph={runGraph}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
            />
        </ReactFlowProvider>
    );
}

interface Dict {
    [key: string]: string | number | boolean;
}

export interface NodeLayoutConfig {
    id: string;
    data: {
        label: string;
        description: string;
        type: string;
        dependencies: NodeDependency[] | null;
        run: RunStep | null;
    };
    width: number;
    height: number;
    type: string;
    targetPosition?: string;
    sourcePosition?: string;
    draggable?: boolean;
    x?: number;
    y?: number;
}

interface EdgeLayoutConfig {
    id: string;
    source: string;
    target: string;
}

const defaultElkOptions = {
    "elk.algorithm": "layered",
    "elk.layered.nodePlacement.strategy": "SIMPLE",
    "elk.layered.nodePlacement.bk.fixedAlignment": "BALANCED",
    "elk.layered.spacing.nodeNodeBetweenLayers": 50,
    "elk.spacing.nodeNode": 80,
    "elk.aspectRatio": 1.0,
    "elk.center": true,
    "elk.direction": "RIGHT",
};

const NodeTypeMapping = {
    TRANSFORM: "common",
    CONNECTION: "common",
    DATA_INPUT: "common",
    BRANCH: "common",
    TERMINATE: "terminate",
    INPUT: "entry",
};

function makeNode(node: RunNode): NodeLayoutConfig {
    // TODO: Make the node width and height dynamic.
    const nodeWidth = 210;
    const nodeHeight = 42;

    let nodeConfig: NodeLayoutConfig = {
        id: node.name,
        data: {
            label: node.name,
            description: node.description,
            type: node.node_type,
            dependencies: node.dependencies,
            run: node.run,
        },
        type: "default",

        // Hardcode a width and height for elk to use when layouting.
        width: nodeWidth,
        height: nodeHeight,

        draggable: false,
    };

    if (Object.keys(NodeTypeMapping).includes(node.node_type)) {
        nodeConfig.type = NodeTypeMapping[node.node_type];
    } else {
        nodeConfig.targetPosition = "left";
        nodeConfig.sourcePosition = "right";
    }

    return nodeConfig;
}

function makeEdges(node: RunNode): any[] {
    if (node.dependencies === null) {
        return [];
    }

    function __makeEdges(node: NodeDefinition): EdgeLayoutConfig[] {
        return node.dependencies.flatMap((dep: any) => {
            // TODO: If `dep` is an object, it means that it comes from
            // a specific output of a node. For now, we discard it, as
            // we don't display the node outputs.
            if (typeof dep === "object" && dep !== null) {
                dep = dep.node;
            }

            let edge: EdgeLayoutConfig = {
                id: `${dep}-${node.name}`,
                source: dep,
                target: node.name,
            };

            return edge;
        });
    }

    return __makeEdges(node);
}

async function layoutGraph(runGraph: RunNode[]): Promise<[NodeLayoutConfig[], EdgeLayoutConfig[]]> {
    const structuredNodes = runGraph.map((node) => makeNode(node));
    const edges = runGraph.flatMap((node) => makeEdges(node));
    const elk = new ELK();

    const [layoutedNodes, layoutedEdges] = await getLayoutedElements(
        structuredNodes,
        edges,
        elk,
        defaultElkOptions,
    );
    return [layoutedNodes, layoutedEdges];
}

async function getLayoutedElements(
    nodes: NodeLayoutConfig[],
    edges: EdgeLayoutConfig[],
    elk: any,
    options: Dict,
): Promise<[NodeLayoutConfig[], EdgeLayoutConfig[]]> {
    const graph = {
        id: "root",
        layoutOptions: options,
        children: [{ id: "all", layoutOptions: options, children: nodes }],
        edges: edges,
    };

    return elk
        .layout(graph)
        .then((layoutedGraph: any) => {
            const format_node = (node: NodeLayoutConfig) => ({
                ...node,
                // React Flow expects a position property on the node instead of `x`
                // and `y` fields.
                position: { x: node.x, y: node.y },
            });

            let nodes = layoutedGraph.children[0].children;
            nodes = nodes.map((n: NodeLayoutConfig) => format_node(n));
            nodes = nodes.filter((node: NodeLayoutConfig) => node.id !== "all");

            return [nodes, edges];
        })
        .catch(console.error);
}
