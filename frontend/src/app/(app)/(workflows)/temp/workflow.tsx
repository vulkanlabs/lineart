"use client";

import { nanoid } from "nanoid";
import React, { useState, useLayoutEffect, useCallback } from "react";
import { Rocket, ArrowRightFromLine, Split, ArrowDown01, Code2 } from "lucide-react";
import {
    ReactFlow,
    ReactFlowProvider,
    MiniMap,
    Controls,
    ConnectionLineType,
    useConnection,
    Background,
    BackgroundVariant,
    addEdge,
    getOutgoers,
    useNodesState,
    useEdgesState,
    useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { NodeHeaderDemo } from "./nodes/node-header-demo";
import { useDropdown } from "./hooks/use-dropdown";

import { nodesConfig, nodeTypes, iconMapping, createNodeByType } from "./nodes";

const defaultNodes = [
    createNodeByType({
        type: "input-node",
        position: { x: 200, y: 200 },
    }),
];

function VulkanWorkflow({ onNodeClick, onPaneClick }) {
    const [nodes, setNodes, onNodesChange] = useNodesState(defaultNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView, getNodes, getEdges, screenToFlowPosition } = useReactFlow();

    const [dropdownPosition, setDropdownPosition] = useState({ x: 0, y: 0 });
    const { isOpen, toggleDropdown, ref } = useDropdown();

    // const connectionState = useConnection();

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

    const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), []);

    const onConnectEnd = useCallback(
        (event, connectionState) => {
            // when a connection is dropped on the pane it's not valid
            if (!connectionState.isValid) {
                // we need to remove the wrapper bounds, in order to get the correct position
                const { clientX, clientY } =
                    "changedTouches" in event ? event.changedTouches[0] : event;

                setDropdownPosition({ x: clientX, y: clientY });
                toggleDropdown();
            }
        },
        [screenToFlowPosition],
    );

    function onAddNode(type: any) {
        console.log(`Adding node of type ${type}`);
        const id = nanoid();
        const newNode = createNodeByType({
            id: id,
            type: type,
            position: screenToFlowPosition({
                x: dropdownPosition.x,
                y: dropdownPosition.y,
            }),
        });
        setNodes((nds) => nds.concat(newNode));
        // setEdges((eds) => eds.concat({ id, source: connectionState.fromNode.id, target: id }));
    }

    return (
        <div className="w-full h-full">
            {isOpen && (
                <div
                    ref={ref}
                    className="absolute z-50"
                    style={{
                        top: `${dropdownPosition.y}px`,
                        left: `${dropdownPosition.x}px`,
                        transform: "translate(-50%, -50%)",
                    }}
                >
                    <AppDropdownMenu
                        onAddNode={onAddNode}
                        filterNodes={(node: any) => node.id != "input-node"}
                    />
                </div>
            )}
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={clickNode}
                onPaneClick={clickPane}
                onConnect={onConnect}
                onConnectEnd={onConnectEnd}
                nodeTypes={nodeTypes}
                // connectionLineType={ConnectionLineType.SmoothStep}
                isValidConnection={isValidConnection}
                fitViewOptions={{ maxZoom: 1 }}
                fitView
            >
                <Background color="#ccc" variant={BackgroundVariant.Dots} />
                <MiniMap nodeStrokeWidth={3} zoomable pannable />
                <Controls />
            </ReactFlow>
        </div>
    );
}

const compatibleNodeTypes = (type: "source" | "target") => {
    if (type === "source") {
        return (node: any) => {
            return (
                node.id === "transform-node" ||
                node.id === "join-node" ||
                node.id === "branch-node" ||
                node.id === "output-node"
            );
        };
    }
    return (node: any) => {
        return (
            node.id === "transform-node" ||
            node.id === "join-node" ||
            node.id === "branch-node" ||
            node.id === "initial-node"
        );
    };
};

function AppDropdownMenu({
    onAddNode,
    filterNodes = () => true,
}: {
    onAddNode: (type: any) => void;
    filterNodes?: (node: any) => boolean;
}) {
    return (
        <DropdownMenu open>
            <DropdownMenuTrigger />
            <DropdownMenuContent className="w-64">
                <DropdownMenuLabel>Nodes</DropdownMenuLabel>
                {Object.values(nodesConfig)
                    .filter(filterNodes)
                    .map((item) => {
                        const IconComponent = item?.icon ? iconMapping[item.icon] : undefined;
                        return (
                            <a key={item.title} onMouseDown={() => onAddNode(item.id)}>
                                <DropdownMenuItem className="flex items-center space-x-2">
                                    {IconComponent ? (
                                        <IconComponent aria-label={item?.icon} />
                                    ) : null}
                                    <span>New {item.title}</span>
                                </DropdownMenuItem>
                            </a>
                        );
                    })}
            </DropdownMenuContent>
        </DropdownMenu>
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
