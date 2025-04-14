"use client";
import { useShallow } from "zustand/react/shallow";
import React, { useState, useCallback, useMemo } from "react";
import {
    ReactFlow,
    ReactFlowProvider,
    MiniMap,
    Controls,
    Background,
    BackgroundVariant,
    getOutgoers,
    useReactFlow,
    ControlButton,
    XYPosition,
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
import { createNodeByType, nodesConfig, standardizeNodeName } from "./nodes";
import { iconMapping } from "./icons";
import { nodeTypes } from "./components";
import { WorkflowProvider, useWorkflowStore } from "./store";
import { SaveIcon } from "lucide-react";
import { saveWorkflowSpec } from "./actions";
import { toast } from "sonner";
import { GraphDefinition, VulkanNode, WorkflowState } from "./types";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { NodeDefinitionDict } from "@vulkan-server/NodeDefinitionDict";

type OnNodeClick = (e: React.MouseEvent, node: any) => void;
type OnPaneClick = (e: React.MouseEvent) => void;

type VulkanWorkflowProps = {
    onNodeClick: OnNodeClick;
    onPaneClick: OnPaneClick;
    policyVersionId?: string;
};

function VulkanWorkflow({ onNodeClick, onPaneClick, policyVersionId }: VulkanWorkflowProps) {
    const {
        nodes,
        edges,
        getSpec,
        getInputSchema,
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
            getInputSchema: state.getInputSchema,
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

    const clickNode: OnNodeClick = (e, node) => onNodeClick(e, node);
    const clickPane: OnPaneClick = (e) => onPaneClick(e);

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
        const position = screenToFlowPosition({
            x: dropdownPosition.x,
            y: dropdownPosition.y,
        });
        const nodeId = addNodeByType(type, position);
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
                            const nodes = getNodes();
                            const inputSchema = getInputSchema();
                            saveWorkflowState(policyVersionId, nodes, spec, inputSchema);
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

async function saveWorkflowState(
    policyVersionId: string,
    nodes: VulkanNode[],
    graph: GraphDefinition,
    inputSchema: Record<string, unknown>,
) {
    // Save workflow UI state
    const uiMetadata = Object.fromEntries(
        nodes.map((node) => [
            node.data.name,
            { position: node.position, width: node.width, height: node.height },
        ]),
    );

    // Filter out INPUT nodes and include positions in metadata
    const graphNodes = Object.entries(graph)
        .filter(([_, node]) => node.node_type !== "INPUT")
        .map(([_, node]) => {
            return {
                ...node,
                metadata: node.metadata,
            };
        });
    
    const result = await saveWorkflowSpec(policyVersionId, graphNodes, uiMetadata, inputSchema);

    if (result.success) {
        toast("Workflow saved ", {
            description: `Workflow saved successfully.`,
            duration: 2000,
            dismissible: true,
        });
    } else {
        console.error("Error saving workflow:", result);
        toast("Failed to save workflow", {
            description: result.error,
            duration: 5000,
        });
    }
}

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
    const nodes = policyVersion.spec.nodes || [];
    const edges = makeEdgesFromDependencies(nodes);

    // Create a proper initial state by validating the incoming spec
    const initialState: WorkflowState = useMemo(() => {
        // If no spec is given or nodes are empty, return default state
        if (!policyVersion.spec || !Array.isArray(nodes) || nodes.length === 0) {
            return defaultState;
        }

        const uiMetadata = policyVersion.ui_metadata;

        // Map server nodes to ReactFlow node format
        const flowNodes = nodes.map((node) => {
            const nodeUIMetadata = uiMetadata ? uiMetadata[node.name] : null;
            const position: XYPosition = nodeUIMetadata.position;
            const height = nodeUIMetadata.height;
            const width = nodeUIMetadata.width;

            const nodeType = node.node_type as keyof typeof iconMapping;
            return {
                id: standardizeNodeName(node.name),
                type: nodeType,
                height: height,
                width: width,
                data: {
                    name: node.name,
                    icon: nodeType,
                    metadata: node.metadata || {},
                },
                position: position,
            };
        });

        return {
            // Always include the input node at the beginning of the nodes array
            nodes: [inputNode, ...flowNodes],
            edges: edges,
        };
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

// Always start with the input node
const inputNode = createNodeByType({
    type: "INPUT",
    position: { x: 200, y: 200 },
    existingNodes: [],
});

const defaultState: WorkflowState = {
    nodes: [inputNode],
    edges: [],
};

function makeEdgesFromDependencies(nodes: NodeDefinitionDict[]): Edge[] {
    // Return early if nodes array is empty or invalid
    if (!nodes || nodes.length === 0) {
        return [];
    }

    const allNodes: NodeDefinitionDict[] = [
        ...nodes,
        { name: "input_node", node_type: "INPUT" } as NodeDefinitionDict,
    ];
    const edgeList = [];

    // Process each node's dependencies
    allNodes.forEach((node) => {
        // Skip if node has no dependencies
        if (!node.dependencies) {
            return;
        }

        const target = standardizeNodeName(node.name);
        const targetHandle = null;

        Object.entries(node.dependencies).forEach(([_, dep]) => {
            const source = standardizeNodeName(dep.node);
            let sourceHandle = null;

            // If the output is specified, we need to find the corresponding
            // handle index in the node.
            if (dep.output) {
                const sourceNode = nodes.find((n) => n.name === dep.node);
                if (!sourceNode) {
                    console.error(`Node ${dep.node} not found`);
                    return;
                }

                // Check if the source node has the specified output and get its index
                const outputIndex = sourceNode.metadata.choices.findIndex(
                    (output) => output === dep.output,
                );
                if (outputIndex === -1) {
                    console.error(`Output ${dep.output} not found in node ${dep.node}`);
                    return;
                }

                sourceHandle = outputIndex;
            }

            // Skip if source is the same as target
            if (source === target) {
                return;
            }

            // Create edge object
            const edge = {
                id: `${source}-${target}`,
                source: source,
                target: target,
                sourceHandle: sourceHandle ? `${sourceHandle}` : null,
                targetHandle: targetHandle || null,
                type: "default",
            };

            // Add edge to the list
            edgeList.push(edge);
        });
    });

    return edgeList;
}
