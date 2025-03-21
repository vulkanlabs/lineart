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
    getOutgoers,
    useNodesState,
    useEdgesState,
    useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { NodeHeaderDemo } from "./nodes";

const nodeTypes = {
    nodeHeaderNode: NodeHeaderDemo,
};

const defaultNodes = [
    {
        id: "1",
        type: "nodeHeaderNode",
        position: { x: 200, y: 200 },
        data: {},
    },
];

function VulkanWorkflow({ onNodeClick, onPaneClick }) {
    const [nodes, setNodes, onNodesChange] = useNodesState(defaultNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView, getNodes, getEdges } = useReactFlow();

    const clickNode = (e, node) => {};

    const clickPane = (e) => {};

    const isValidConnection = useCallback(
        (connection) => {
          // we are using getNodes and getEdges helpers here
          // to make sure we create isValidConnection function only once
          const nodes = getNodes();
          const edges = getEdges();
          const target = nodes.find((node) => node.id === connection.target);
          const hasCycle = (node, visited = new Set()) => {
            if (visited.has(node.id)) return false;
     
            visited.add(node.id);
     
            for (const outgoer of getOutgoers(node, nodes, edges)) {
              if (outgoer.id === connection.source) return true;
              if (hasCycle(outgoer, visited)) return true;
            }
          };
     
          if (target.id === connection.source) return false;
          return !hasCycle(target);
        },
        [getNodes, getEdges],
      );

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
            isValidConnection={isValidConnection}
            fitViewOptions={{ maxZoom: 1 }}
            fitView
        >
            <Background color="#ccc" variant={BackgroundVariant.Dots} />
            <MiniMap nodeStrokeWidth={3} zoomable pannable />
            <Controls />
        </ReactFlow>
    );
}

export default function WorkflowFrame() {
    return (
        <ReactFlowProvider>
            <VulkanWorkflow
                onNodeClick={(_: any, node: any) => console.log(node)}
                onPaneClick={() => console.log("pane")}
            />
        </ReactFlowProvider>
    );
}
