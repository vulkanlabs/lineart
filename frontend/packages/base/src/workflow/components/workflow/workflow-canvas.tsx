"use client";

import React, { useState, useCallback, useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { SaveIcon, ChevronDownIcon, ChevronUpIcon, LayoutIcon, CopyIcon } from "lucide-react";
import {
    ReactFlow,
    Controls,
    Background,
    BackgroundVariant,
    useReactFlow,
    ControlButton,
} from "@xyflow/react";

import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@vulkanlabs/base/ui";

import { useDropdown } from "@/workflow/hooks/use-dropdown";
import { nodesConfig } from "@/workflow/utils/nodes";
import { iconMapping } from "@/workflow/icons";
import { useWorkflowStore } from "@/workflow/store";
import { useWorkflowApi, Workflow } from "@/workflow/api";
import {
    getLayoutedNodes,
    defaultElkOptions,
    type UnlayoutedVulkanNode,
} from "@/workflow/utils/layout";

/**
 * Props for the workflow canvas component
 */
export type WorkflowCanvasProps = {
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
    workflow: Workflow;
    nodeTypes: Record<string, React.ComponentType<any>>;
    toast?: (message: string, options?: any) => void;
    onRefresh?: () => void;
};

/**
 * Main workflow canvas component with ReactFlow integration
 */
export function WorkflowCanvas({
    onNodeClick = () => {},
    onPaneClick = () => {},
    workflow,
    nodeTypes,
    toast = console.log,
    onRefresh = () => {},
}: WorkflowCanvasProps) {
    const api = useWorkflowApi();

    const {
        nodes,
        edges,
        getSpec,
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

    const clickNode = (e: React.MouseEvent, node: any) => onNodeClick(e, node);
    const clickPane = (e: React.MouseEvent) => onPaneClick(e);

    /**
     * Initialize the workflow layout when component mounts
     */
    const onInit = useCallback(() => {
        if (!workflow.ui_metadata) {
            const unpositionedNodes: UnlayoutedVulkanNode[] = nodes.map((node) => ({
                ...node,
                layoutOptions: defaultElkOptions,
            }));

            getLayoutedNodes(unpositionedNodes, edges, defaultElkOptions).then((layoutedNodes) => {
                const nodesMap = Object.fromEntries(layoutedNodes.map((node) => [node.id, node]));
                const newNodes = nodes.map((node) => ({
                    ...node,
                    position: nodesMap[node.id].position,
                }));
                setNodes(newNodes);
                // Fit the view after nodes are positioned
                setTimeout(() => fitView(), 0);
            });
        } else {
            // Also fit view when ui_metadata exists
            setTimeout(() => fitView(), 0);
        }
    }, [workflow, nodes, edges, setNodes, fitView]);

    /**
     * Handle connection end events for node creation dropdown
     */
    const onConnectEnd = useCallback(
        (event: any, connectionState: any) => {
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

    /**
     * Add a new node and connect it to the current connection
     */
    function onAddNode(type: string) {
        const position = screenToFlowPosition({
            x: dropdownPosition.x,
            y: dropdownPosition.y,
        });
        const nodeId = addNodeByType(type as any, position);
        if (nodeId && connectingHandle) {
            onConnect({
                source: connectingHandle.nodeId,
                target: nodeId,
                sourceHandle: connectingHandle.id,
                targetHandle: null,
            });
        }
    }

    /**
     * Check if all nodes are currently collapsed
     */
    const areAllNodesCollapsed = useMemo(() => {
        return nodes.every((node) => node.data?.detailsExpanded === false);
    }, [nodes]);

    /**
     * Apply automatic layout to all nodes
     */
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

    /**
     * Copy workflow specification to clipboard
     */
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
    }, [getSpec, toast]);

    /**
     * Save the current workflow state
     */
    const saveWorkflow = useCallback(async () => {
        try {
            const spec = getSpec();
            const currentNodes = getNodes();

            // Save workflow UI state
            const uiMetadata = Object.fromEntries(
                currentNodes.map((node) => [
                    node.data.name,
                    { position: node.position, width: node.width, height: node.height },
                ]),
            );

            const result = await api.saveWorkflowSpec(workflow, spec, uiMetadata);

            if (result.success) {
                toast("Workflow saved", {
                    description: "Workflow saved successfully.",
                    duration: 2000,
                    dismissible: true,
                });
                onRefresh();
            } else {
                toast("Failed to save workflow", {
                    description: result.error,
                    duration: 5000,
                });
            }
        } catch (error) {
            console.error("Error saving workflow:", error);
            toast("Failed to save workflow", {
                description: error instanceof Error ? error.message : "Unknown error",
                duration: 5000,
            });
        }
    }, [api, workflow, getSpec, getNodes, toast, onRefresh]);

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
                    <NodeCreationDropdown
                        onAddNode={onAddNode}
                        filterNodes={(node: any) => node.id !== "INPUT"}
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
                proOptions={{ hideAttribution: true }}
            >
                <Background
                    color="#c8c8c8"
                    bgColor="#fafafa"
                    size={3}
                    gap={30}
                    variant={BackgroundVariant.Dots}
                />
                <Controls showZoom={false} showInteractive={false} orientation="horizontal">
                    <ControlButton onClick={saveWorkflow}>
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

/**
 * Props for the node creation dropdown
 */
type NodeCreationDropdownProps = {
    onAddNode: (type: string) => void;
    filterNodes?: (node: any) => boolean;
};

/**
 * Dropdown menu for creating new nodes
 */
function NodeCreationDropdown({ onAddNode, filterNodes = () => true }: NodeCreationDropdownProps) {
    return (
        <DropdownMenu open>
            <DropdownMenuTrigger />
            <DropdownMenuContent className="w-64">
                <DropdownMenuLabel>Nodes</DropdownMenuLabel>
                {Object.values(nodesConfig)
                    .filter(filterNodes)
                    .map((item) => {
                        const IconComponent = item?.icon
                            ? iconMapping[item.icon as keyof typeof iconMapping]
                            : undefined;
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
