"use client";

import { useShallow } from "zustand/react/shallow";
import React, { useState, useLayoutEffect, useCallback, useEffect, useMemo } from "react";
import {
    ReactFlow,
    ReactFlowProvider,
    MiniMap,
    Controls,
    ConnectionLineType,
    Background,
    BackgroundVariant,
    getOutgoers,
    useReactFlow,
    ControlButton,
    type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useDropdown } from "./hooks/use-dropdown";
import { createNodeByType, nodesConfig } from "./nodes";
import { iconMapping } from "./icons";
import { nodeTypes } from "./components";
import { WorkflowProvider, useWorkflowStore } from "./store";
import { SaveIcon } from "lucide-react";
import { saveWorkflowSpec } from "./actions";
import { toast } from "sonner";
import { GraphDefinition, WorkflowState, VulkanNode } from "./types";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

type VulkanWorkflowProps = {
    onNodeClick: (e: React.MouseEvent, node: any) => void;
    onPaneClick: (e: React.MouseEvent) => void;
    policyVersionId?: string;
};

function VulkanWorkflow({ onNodeClick, onPaneClick, policyVersionId }: VulkanWorkflowProps) {
    const {
        nodes,
        edges,
        getSpec,
        addNodeByType,
        getNodes,
        getEdges,
        onNodesChange,
        onEdgesChange,
        onConnect,
    } = useWorkflowStore(
        useShallow((state) => ({
            nodes: state.nodes,
            edges: state.edges,
            getSpec: state.getSpec,
            addNodeByType: state.addNodeByType,
            getNodes: state.getNodes,
            getEdges: state.getEdges,
            onNodesChange: state.onNodesChange,
            onEdgesChange: state.onEdgesChange,
            onConnect: state.onConnect,
        })),
    );

    const { screenToFlowPosition } = useReactFlow();

    const [dropdownPosition, setDropdownPosition] = useState({ x: 0, y: 0 });
    const { isOpen, connectingHandle, toggleDropdown, ref } = useDropdown();

    useEffect(() => {
        console.log(JSON.stringify(getSpec()));
    }, [nodes]);

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

    const onConnectEnd = useCallback((event, connectionState) => {
        // when a connection is dropped on the pane it's not valid
        if (!connectionState.isValid) {
            // we need to remove the wrapper bounds, in order to get the correct position
            const { clientX, clientY } =
                "changedTouches" in event ? event.changedTouches[0] : event;

            setDropdownPosition({ x: clientX, y: clientY });
            toggleDropdown(connectionState.fromHandle);
        }
    }, []);

    function onAddNode(type: any) {
        const nodeId = addNodeByType(
            type,
            screenToFlowPosition({
                x: dropdownPosition.x,
                y: dropdownPosition.y,
            }),
        );
        onConnect({
            source: connectingHandle.nodeId,
            target: nodeId,
            sourceHandle: connectingHandle.id,
            targetHandle: null,
        });
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
                        transform: "translate(0, -100%)",
                    }}
                >
                    <AppDropdownMenu
                        onAddNode={onAddNode}
                        filterNodes={(node: any) => node.id != "INPUT"}
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
                fitView
                proOptions={{ hideAttribution: true }}
            >
                <Background color="#ccc" variant={BackgroundVariant.Dots} />
                <MiniMap nodeStrokeWidth={3} zoomable pannable />
                <Controls showZoom={false} showInteractive={false} orientation="horizontal">
                    <ControlButton
                        onClick={() => {
                            const spec = getSpec();
                            saveWorkflowState(policyVersionId, spec);
                        }}
                    >
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger>
                                    <SaveIcon />
                                </TooltipTrigger>
                                <TooltipContent>Save</TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </ControlButton>
                </Controls>
            </ReactFlow>
        </div>
    );
}

async function saveWorkflowState(policyVersionId: string, graph: GraphDefinition) {
    const graphNodes = Object.values(graph).filter((node) => node.node_type !== "INPUT");
    const result = await saveWorkflowSpec(policyVersionId, graphNodes);

    if (result.success) {
        toast("Workflow saved ", {
            description: `Workflow saved successfully.`,
            duration: 2000,
            dismissible: true,
        });
    } else {
        console.error("Error saving workflow:", result);
        alert("Failed to save workflow: " + result.error);
    }
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
                            <a key={item.name} onMouseDown={() => onAddNode(item.id)}>
                                <DropdownMenuItem className="flex items-center space-x-2">
                                    {IconComponent ? (
                                        <IconComponent aria-label={item?.icon} />
                                    ) : null}
                                    <span>New {item.name}</span>
                                </DropdownMenuItem>
                            </a>
                        );
                    })}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

export default function WorkflowFrame({ policyVersion }: { policyVersion: PolicyVersion }) {
    const policyVersionId = policyVersion.policy_version_id;
    const typedPolicyVersion = policyVersion as WorkflowPolicyVersion;
    const nodes = typedPolicyVersion.spec.nodes;

    // Create a proper initial state by validating the incoming spec
    const initialState: WorkflowState = useMemo(() => {
        // Check if spec exists and has valid nodes array
        if (policyVersion?.spec && Array.isArray(nodes) && nodes.length > 0) {
            console.log("Nodes", nodes);
            const positionedNodes = nodes.map((node) => {
                return {
                    id: node.id || node.name,
                    type: node.type,
                    data: {
                        name: node.name,
                        icon: node.type,
                        minHeight: 50,
                        minWidth: 100,
                        metadata: node.metadata,
                    },
                    position: {
                        x: 0,
                        y: 0,
                    },
                };
            });
            console.log("positionedNodes", positionedNodes);
            return {
                nodes: positionedNodes,
                edges: [],
            };
        }

        // Fall back to default state if spec is invalid
        return defaultState;
    }, [policyVersion]);

    return (
        <ReactFlowProvider>
            <WorkflowProvider initialState={initialState}>
                <VulkanWorkflow
                    onNodeClick={(_: any, node: any) => console.log(node)}
                    onPaneClick={() => console.log("pane")}
                    policyVersionId={policyVersionId}
                />
            </WorkflowProvider>
        </ReactFlowProvider>
    );
}

const inputNode = createNodeByType({
    type: "INPUT",
    position: { x: 200, y: 200 },
});

const defaultState: WorkflowState = {
    nodes: [inputNode],
    edges: [],
};
