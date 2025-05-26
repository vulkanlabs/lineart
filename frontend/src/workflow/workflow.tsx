"use client";
import React, { useState, useCallback, useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { SaveIcon, ChevronDownIcon, ChevronUpIcon, LayoutIcon, CopyIcon } from "lucide-react";
import { toast } from "sonner";
import ELK from "elkjs/lib/elk.bundled.js";
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
    Connection,
    getIncomers,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { PolicyVersion } from "@vulkan-server/PolicyVersion";
import { NodeDefinitionDict } from "@vulkan-server/NodeDefinitionDict";
import { UIMetadata } from "@vulkan-server/UIMetadata";

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
import { saveWorkflowSpec } from "./actions";
import { BranchNodeMetadata, GraphDefinition, VulkanNode, WorkflowState } from "./types";

type OnNodeClick = (e: React.MouseEvent, node: any) => void;
type OnPaneClick = (e: React.MouseEvent) => void;

type VulkanWorkflowProps = {
    onNodeClick: OnNodeClick;
    onPaneClick: OnPaneClick;
    policyVersion?: PolicyVersion;
};

function VulkanWorkflow({ onNodeClick, onPaneClick, policyVersion }: VulkanWorkflowProps) {
    const {
        nodes,
        edges,
        getSpec,
        getInputSchema,
        addNodeByType,
        getNodes,
        setNodes,
        onNodesChange,
        onEdgesChange,
        onConnect,
        toggleAllNodesCollapsed,
    } = useWorkflowStore(
        useShallow((state) => ({
            nodes: state.nodes,
            edges: state.edges,
            getSpec: state.getSpec,
            getInputSchema: state.getInputSchema,
            addNodeByType: state.addNodeByType,
            getNodes: state.getNodes,
            setNodes: state.setNodes,
            onNodesChange: state.onNodesChange,
            onEdgesChange: state.onEdgesChange,
            onConnect: state.onConnect,
            toggleAllNodesCollapsed: state.toggleAllNodesCollapsed,
        })),
    );

    const { screenToFlowPosition, fitView } = useReactFlow();

    const [dropdownPosition, setDropdownPosition] = useState({ x: 0, y: 0 });
    const { isOpen, connectingHandle, toggleDropdown, ref } = useDropdown();

    const clickNode: OnNodeClick = (e, node) => onNodeClick(e, node);
    const clickPane: OnPaneClick = (e) => onPaneClick(e);

    const onInit = useCallback(() => {
        if (!policyVersion.ui_metadata) {
            let unpositionedNodes: UnlayoutedVulkanNode[] = nodes.map((node) => {
                return {
                    ...node,
                    layoutOptions: defaultElkOptions,
                };
            });

            getLayoutedNodes(unpositionedNodes, edges, defaultElkOptions).then(
                (layoutedNodes: any) => {
                    const nodesMap = Object.fromEntries(
                        layoutedNodes.map((node) => [node.id, node]),
                    );
                    const newNodes = nodes.map((node) => {
                        return {
                            ...node,
                            position: nodesMap[node.id].position,
                        };
                    });
                    setNodes(newNodes);
                    // Fit the view after nodes are positioned
                    setTimeout(() => fitView(), 0);
                },
            );
        } else {
            // Also fit view when ui_metadata exists
            setTimeout(() => fitView(), 0);
        }
    }, [policyVersion, nodes, edges, setNodes, fitView]);

    const onConnectEnd = useCallback(
        (event, connectionState) => {
            // when a connection is dropped on the pane it's not valid
            if (!connectionState.isValid) {
                // we need to remove the wrapper bounds, in order to get the correct position
                const { clientX, clientY } =
                    "changedTouches" in event ? event.changedTouches[0] : event;

                setDropdownPosition({ x: clientX, y: clientY });
                toggleDropdown(connectionState.fromHandle);
            }
        },
        [toggleDropdown],
    );

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

    const areAllNodesCollapsed = useMemo(() => {
        return nodes.every((node) => node.data?.detailsExpanded === false);
    }, [nodes]);

    const autoLayoutNodes = useCallback(async () => {
        const unpositionedNodes: UnlayoutedVulkanNode[] = nodes.map((node) => ({
            ...node,
            layoutOptions: defaultElkOptions,
        }));

        try {
            const layoutedNodes = await getLayoutedNodes(
                unpositionedNodes,
                edges,
                defaultElkOptions,
            );
            const nodesMap = Object.fromEntries(layoutedNodes.map((node) => [node.id, node]));
            const newNodes = nodes.map((node) => ({
                ...node,
                position: nodesMap[node.id].position,
            }));
            setNodes(newNodes);
            setTimeout(() => fitView(), 0);
        } catch (error) {
            console.error("Error applying auto-layout:", error);
        }
    }, [nodes, edges, setNodes, fitView]);

    const copySpecToClipboard = useCallback(async () => {
        try {
            const spec = getSpec();
            const jsonString = JSON.stringify(spec, null, 2);
            await navigator.clipboard.writeText(jsonString);
            toast("Specification copied", {
                description: "Workflow specification copied to clipboard",
                duration: 2000,
                dismissible: true,
            });
        } catch (error) {
            console.error("Failed to copy specification:", error);
            toast("Failed to copy", {
                description: "Could not copy specification to clipboard",
                duration: 3000,
            });
        }
    }, [getSpec]);

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
                onInit={onInit}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={clickNode}
                onPaneClick={clickPane}
                onConnect={onConnect}
                onConnectEnd={onConnectEnd}
                nodeTypes={nodeTypes}
                minZoom={0.1}
                // connectionLineType={ConnectionLineType.SmoothStep}
                // isValidConnection={isValidConnection}
                // fitView
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
                            saveWorkflowState(policyVersion, nodes, spec, inputSchema);
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
                    <ControlButton onClick={toggleAllNodesCollapsed}>
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger>
                                    {areAllNodesCollapsed ? <ChevronDownIcon /> : <ChevronUpIcon />}
                                </TooltipTrigger>
                                <TooltipContent>
                                    {areAllNodesCollapsed ? "Expand All" : "Collapse All"}
                                </TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </ControlButton>
                    <ControlButton onClick={autoLayoutNodes}>
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger>
                                    <LayoutIcon />
                                </TooltipTrigger>
                                <TooltipContent>Auto Layout</TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </ControlButton>
                    <ControlButton onClick={copySpecToClipboard}>
                        <TooltipProvider>
                            <Tooltip>
                                <TooltipTrigger>
                                    <CopyIcon />
                                </TooltipTrigger>
                                <TooltipContent>Copy Specification</TooltipContent>
                            </Tooltip>
                        </TooltipProvider>
                    </ControlButton>
                </Controls>
            </ReactFlow>
        </div>
    );
}

async function saveWorkflowState(
    policyVersion: PolicyVersion,
    nodes: VulkanNode[],
    graph: GraphDefinition,
    inputSchema: { [key: string]: string },
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

    const result = await saveWorkflowSpec(policyVersion, graphNodes, uiMetadata, inputSchema);

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
                            <a key={item.name} onMouseDown={() => onAddNode(item.id.trim())}>
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

function getDefaultUIMetadata(nodeType: string) {
    const nodeConfig = nodesConfig[nodeType];
    return {
        position: { x: 0, y: 0 },
        width: nodeConfig.width,
        height: nodeConfig.height,
    };
}

export default function WorkflowFrame({ policyVersion }: { policyVersion: PolicyVersion }) {
    const initialState: WorkflowState = useMemo(() => {
        const uiMetadata = policyVersion.ui_metadata || {};
        const inputNode = makeInputNode(policyVersion.input_schema, uiMetadata["input_node"]);

        // If no spec is defined, return an empty state: new version
        if (!policyVersion.spec || policyVersion.spec.nodes.length === 0) {
            return defaultWorkflowState(inputNode);
        }

        const nodes = policyVersion.spec.nodes || [];
        const edges = makeEdgesFromDependencies(nodes);

        // Map server nodes to ReactFlow node format
        const flowNodes: VulkanNode[] = nodes.map((node) => {
            const nodeUIMetadata = uiMetadata[node.name] || getDefaultUIMetadata(node.node_type);
            const position: XYPosition = nodeUIMetadata.position;
            const height = nodeUIMetadata.height;
            const width = nodeUIMetadata.width;

            const incomingEdges = edges
                .filter((edge) => edge.target === node.name)
                .reduce((acc: any, edge: any) => {
                    const [key, dependency] = Object.entries(node.dependencies).find(
                        ([, dep]) => dep.node === edge.source,
                    );
                    acc[edge.id] = { key, dependency };
                    return acc;
                }, {});

            const nodeType = node.node_type as keyof typeof iconMapping;
            return {
                id: node.name,
                type: nodeType,
                height: height,
                width: width,
                data: {
                    name: node.name,
                    icon: nodeType,
                    metadata: node.metadata || {},
                    incomingEdges: incomingEdges,
                },
                position: position,
            };
        });

        return {
            nodes: [inputNode, ...flowNodes],
            edges: edges,
        };
    }, [policyVersion]);

    return (
        <ReactFlowProvider>
            <WorkflowProvider initialState={initialState}>
                <VulkanWorkflow
                    onNodeClick={(_: any, node: any) => null}
                    onPaneClick={() => null}
                    policyVersion={policyVersion}
                />
            </WorkflowProvider>
        </ReactFlowProvider>
    );
}

function makeInputNode(inputSchema: { [key: string]: string }, inputNodeUIMetadata: UIMetadata) {
    // Create the input node with proper metadata if available
    let inputNode = defaultInputNode;
    if (inputNodeUIMetadata) {
        inputNode = {
            ...inputNode,
            position: inputNodeUIMetadata?.position,
            width: inputNodeUIMetadata?.width,
        };
    }
    if (inputSchema) {
        inputNode = {
            ...inputNode,
            data: {
                ...inputNode.data,
                metadata: {
                    ...inputNode.data.metadata,
                    schema: inputSchema,
                },
            },
        };
    }
    return inputNode;
}

const defaultInputNode = createNodeByType({
    type: "INPUT",
    position: { x: 200, y: 200 },
    existingNodes: [],
});

// Always start with the input node
const defaultWorkflowState = (inputNode: VulkanNode) => {
    return {
        nodes: [inputNode],
        edges: [],
    };
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

        const target = node.name;
        const targetHandle = null;

        Object.entries(node.dependencies).forEach(([_, dep]) => {
            const source = dep.node;
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
                const sourceMetadata = sourceNode.metadata as BranchNodeMetadata;
                const outputIndex = sourceMetadata.choices.findIndex(
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

type UnlayoutedVulkanNode = VulkanNode & {
    layoutOptions?: any;
};

async function getLayoutedNodes(nodes: any[], edges: any[], options: any): Promise<any[]> {
    const elk = new ELK();
    const graph = {
        id: "root",
        layoutOptions: options,
        children: [{ id: "all", layoutOptions: options, children: nodes }],
        edges: edges,
    };

    return elk
        .layout(graph)
        .then((layoutedGraph: any) => {
            const format_node = (node: any) => ({
                ...node,
                // React Flow expects a position property on the node instead of `x`
                // and `y` fields.
                position: { x: node.x, y: node.y },
            });

            const extractChildren = (node: any) => {
                if (node.children) {
                    const children = node.children.flatMap((child: any) => extractChildren(child));
                    return [format_node(node), ...children];
                }
                return format_node(node);
            };

            let nodes = layoutedGraph.children.flatMap((node: any) => extractChildren(node));
            nodes = nodes.filter((node: any) => node.id !== "all");

            return nodes;
        })
        .catch(console.error);
}
