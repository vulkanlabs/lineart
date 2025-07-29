"use client";

import React, { useState, useCallback, useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { SaveIcon, ChevronDownIcon, ChevronUpIcon, LayoutIcon, CopyIcon, FocusIcon } from "lucide-react";
import { ToolbarIcon } from "./toolbar-icon";
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
    workflow: Workflow;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
    nodeTypes: Record<string, React.ComponentType<any>>;
    toast?: (message: string, options?: any) => void;
    onRefresh?: () => void;
};

/**
 * Main workflow canvas component with ReactFlow integration
 */
export function WorkflowCanvas({
    workflow,
    onNodeClick = () => {},
    onPaneClick = () => {},
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

    const { screenToFlowPosition, fitView, getZoom, setViewport, getViewport } = useReactFlow();

    const [dropdownPosition, setDropdownPosition] = useState({ x: 0, y: 0 });
    const { isOpen, connectingHandle, toggleDropdown, ref } = useDropdown();

    const clickNode = (e: React.MouseEvent, node: any) => onNodeClick(e, node);
    const clickPane = (e: React.MouseEvent) => onPaneClick(e);

    const smartFitView = useCallback(() => {
        if (nodes.length === 0) return;
        
        // Calculate workflow spatial characteristics
        const bounds = nodes.reduce((acc, node) => {
            const x1 = node.position.x;
            const y1 = node.position.y;
            const x2 = x1 + (node.width || 450);
            const y2 = y1 + (node.height || 225);
            
            return {
                minX: Math.min(acc.minX, x1),
                minY: Math.min(acc.minY, y1),
                maxX: Math.max(acc.maxX, x2),
                maxY: Math.max(acc.maxY, y2),
            };
        }, { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity });
        
        const workflowWidth = bounds.maxX - bounds.minX;
        const workflowHeight = bounds.maxY - bounds.minY;
        const screenWidth = window.innerWidth;
        const screenHeight = window.innerHeight;
        
        // Determine complexity based on spatial distribution
        const isSimple = workflowWidth < screenWidth * 0.7 && workflowHeight < screenHeight * 0.7;
        const isMedium = workflowWidth < screenWidth * 1.5 && workflowHeight < screenHeight * 1.5;
        
        if (isSimple) {
            fitView({ padding: 0.1, maxZoom: 1.2, minZoom: 0.5 });
        } else if (isMedium) {
            fitView({ padding: 0.15, maxZoom: 1.0, minZoom: 0.3 });
        } else {
            // too large to fit well, use INPUT-left strategy
            const inputNode = nodes.find(node => node.type === "INPUT");
            if (inputNode) {
                const nodeWidth = inputNode.width || 450;
                const nodeHeight = inputNode.height || 225;
                const leftMargin = 150; 
                
                const nodeCenterX = inputNode.position.x + nodeWidth / 2;
                const nodeCenterY = inputNode.position.y + nodeHeight / 2;
                
                setViewport({
                    x: -nodeCenterX + leftMargin + nodeWidth / 2,
                    y: -nodeCenterY + window.innerHeight / 2,
                    zoom: 0.6
                });
            } else {
                // Fallback: fit all but with limited zoom to keep nodes readable
                fitView({ padding: 0.2, maxZoom: 0.6, minZoom: 0.2 });
            }
        }
    }, [nodes, fitView, setViewport]);

    /**
     * Initialize the workflow layout when component mounts
     */
    const onInit = useCallback((reactFlowInstance) => {
        setTimeout(() => {
            smartFitView();
        }, 0);
        
        if (!workflow.workflow?.ui_metadata) {
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
                // Apply smart fit view after nodes are positioned
                setTimeout(() => {
                    smartFitView();
                }, 100);
            });
        } else {
            // For existing workflows, use smart fit view for consistent UX
            setTimeout(() => {
                smartFitView();
            }, 100);
        }
    }, [workflow, nodes, edges, setNodes, smartFitView]);

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
     * Apply automatic layout to all nodes and fit view
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
            setTimeout(() => {
                smartFitView();
            }, 100);
        } catch (error) {
            console.error("Error applying auto-layout:", error);
        }
    }, [nodes, edges, setNodes, smartFitView]);

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
                defaultZoom={1}
                defaultViewport={{ x: 0, y: 0, zoom: 1 }}
                fitView={false}
                fitViewOptions={{ includeHiddenNodes: false }}
                proOptions={{ hideAttribution: true }}
            >
                <Background
                    color="#c8c8c8"
                    bgColor="#fafafa"
                    size={3}
                    gap={30}
                    variant={BackgroundVariant.Dots}
                />
                <Controls showZoom={false} showInteractive={false} showFitView={false} orientation="horizontal">
                    <ControlButton onClick={saveWorkflow} title="Save">
                        <ToolbarIcon icon={SaveIcon} />
                    </ControlButton>
                    <ControlButton onClick={smartFitView} title="Smart Fit View">
                        <ToolbarIcon icon={FocusIcon} />
                    </ControlButton>
                    <ControlButton 
                        onClick={toggleAllNodesCollapsed}
                        title={areAllNodesCollapsed ? "Expand All" : "Collapse All"}
                    >
                        {areAllNodesCollapsed ? 
                            <ToolbarIcon icon={ChevronDownIcon} /> : 
                            <ToolbarIcon icon={ChevronUpIcon} />
                        }
                    </ControlButton>
                    <ControlButton onClick={autoLayoutNodes} title="Auto Layout">
                        <ToolbarIcon icon={LayoutIcon} />
                    </ControlButton>
                    <ControlButton onClick={copySpecToClipboard} title="Copy Specification">
                        <ToolbarIcon icon={CopyIcon} />
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
