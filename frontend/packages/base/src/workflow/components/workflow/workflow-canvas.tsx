"use client";

import React, { useState, useCallback, useMemo, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { ChevronDownIcon, ChevronUpIcon, LayoutIcon, CopyIcon, FocusIcon } from "lucide-react";
import { ToolbarIcon } from "./toolbar-icon";
import {
    ReactFlow,
    Controls,
    Background,
    BackgroundVariant,
    useReactFlow,
    ControlButton,
    type OnInit,
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
import { Workflow } from "@/workflow/api";
import { getLayoutedNodes, type UnlayoutedVulkanNode } from "@/workflow/utils/layout";
import type { VulkanNode, Edge } from "@/workflow/types/workflow";
import type { WorkflowStore } from "@/workflow/store/store-types";

/**
 * Props for the workflow canvas component
 */
export type WorkflowCanvasProps = {
    workflow: Workflow;
    onNodeClick?: (e: React.MouseEvent, node: VulkanNode) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
    nodeTypes: Record<string, React.ComponentType<any>>;
    toast?: (message: string, options?: any) => void;
    onRefresh?: () => void;
};

/**
 * Main workflow canvas component - the heart of the workflow builder
 * @param {Object} props - Component configuration
 * @param {Workflow} props.workflow - The workflow data structure with nodes and edges
 * @param {Function} [props.onNodeClick] - Called when a node is clicked, useful for selection/editing
 * @param {Function} [props.onPaneClick] - Called when clicking empty canvas area
 * @param {Record<string, React.ComponentType>} props.nodeTypes - Map of node type names to React components
 * @param {Function} [props.toast] - Toast notification function for user feedback
 * @param {Function} [props.onRefresh] - Called to refresh workflow data
 * @param {string} [props.projectId] - Current project context ID
 * @returns {JSX.Element} Full workflow canvas with drag-drop, zoom, pan, save functionality
 */
export function WorkflowCanvas({
    workflow,
    onNodeClick = () => {},
    onPaneClick = () => {},
    nodeTypes,
    toast = console.log,
    onRefresh = () => {},
}: WorkflowCanvasProps) {
    const {
        nodes,
        edges,
        getSpec,
        addNodeByType,
        setNodes,
        onNodesChange,
        onEdgesChange,
        onConnect,
        toggleAllNodesCollapsed,
    } = useWorkflowStore(
        useShallow((state: WorkflowStore) => ({
            nodes: state.nodes,
            edges: state.edges,
            getSpec: state.getSpec,
            addNodeByType: state.addNodeByType,
            setNodes: state.setNodes,
            onNodesChange: state.onNodesChange,
            onEdgesChange: state.onEdgesChange,
            onConnect: state.onConnect,
            toggleAllNodesCollapsed: state.toggleAllNodesCollapsed,
        })),
    );
    console.log("nodes", nodes);

    const { screenToFlowPosition, fitView, setViewport } = useReactFlow();

    const [dropdownPosition, setDropdownPosition] = useState({ x: 0, y: 0 });
    const { isOpen, connectingHandle, toggleDropdown, ref } = useDropdown();

    const clickNode = (e: React.MouseEvent, node: VulkanNode) => onNodeClick(e, node);
    const clickPane = (e: React.MouseEvent) => onPaneClick(e);

    /**
     * Smart fit view algorithm - intelligently fits workflow to screen based on complexity
     *
     * Algorithm breakdown:
     * - Calculate workflow bounding box (total area occupied by all nodes)
     * - Compare workflow size to screen size to determine complexity
     * - Apply different zoom/pan strategies based on complexity:
     *   - Simple workflows: High zoom, centered view
     *   - Medium workflows: Medium zoom, some padding
     *   - Complex workflows: Focus on INPUT node (left-aligned strategy)
     *
     * Large workflows are hard to navigate when fully zoomed out,
     * so we focus on the starting point (INPUT node) for better UX.
     */
    const smartFitView = useCallback(() => {
        if (nodes.length === 0) return;

        // Calculate total workflow bounding box
        // Find the rectangle that contains all nodes by tracking min/max coordinates
        const bounds = nodes.reduce(
            (acc, node) => {
                // Each node occupies a rectangle from (x1,y1) to (x2,y2)
                const x1 = node.position.x;
                const y1 = node.position.y;
                const x2 = x1 + (node.width || 450); // Default width if not set
                const y2 = y1 + (node.height || 225); // Default height if not set

                return {
                    minX: Math.min(acc.minX, x1), // Leftmost point
                    minY: Math.min(acc.minY, y1), // Topmost point
                    maxX: Math.max(acc.maxX, x2), // Rightmost point
                    maxY: Math.max(acc.maxY, y2), // Bottommost point
                };
            },
            { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity },
        );

        // Calculate workflow dimensions and screen dimensions
        const workflowWidth = bounds.maxX - bounds.minX; // Total width of all nodes
        const workflowHeight = bounds.maxY - bounds.minY; // Total height of all nodes
        const screenWidth = window.innerWidth; // Available screen width
        const screenHeight = window.innerHeight; // Available screen height

        // Classify workflow complexity based on size relative to screen
        // These thresholds determine the zoom/pan strategy:
        const isSimple = workflowWidth < screenWidth * 0.7 && workflowHeight < screenHeight * 0.7;
        // Simple: Workflow fits comfortably on screen (< 70% of screen area)

        const isMedium = workflowWidth < screenWidth * 1.5 && workflowHeight < screenHeight * 1.5;
        // Medium: Workflow is larger but still manageable (< 150% of screen area)

        // Apply zoom/pan strategy based on complexity
        if (isSimple) {
            // Simple workflows: High zoom with minimal padding for detailed view
            fitView({ padding: 0.1, maxZoom: 1.2, minZoom: 0.5 });
        } else if (isMedium) {
            // Medium workflows: Moderate zoom with more padding
            fitView({ padding: 0.15, maxZoom: 1.0, minZoom: 0.3 });
        } else {
            // Complex workflows: Use INPUT-left strategy for better navigation
            // Problem: Large workflows are hard to navigate when fully zoomed out
            // Solution: Focus on the starting point (INPUT node) positioned on the left
            const inputNode = nodes.find((node) => node.type === "INPUT");

            if (inputNode) {
                const nodeWidth = inputNode.width || 450;
                const nodeHeight = inputNode.height || 225;
                const leftMargin = 150; // Keep INPUT node away from left edge

                // Calculate INPUT node center for positioning
                const nodeCenterX = inputNode.position.x + nodeWidth / 2;
                const nodeCenterY = inputNode.position.y + nodeHeight / 2;

                // Position INPUT node on left side of screen, vertically centered
                setViewport({
                    x: -nodeCenterX + leftMargin + nodeWidth / 2, // Move INPUT to left margin
                    y: -nodeCenterY + window.innerHeight / 2, // Center vertically
                    zoom: 0.6, // Moderate zoom for readability
                });
            } else {
                // Fallback: No INPUT node found, fit all with limited zoom
                fitView({ padding: 0.2, maxZoom: 0.6, minZoom: 0.2 });
            }
        }
    }, [nodes, fitView, setViewport]);

    /**
     * Initialize workflow layout when component mounts
     *
     * This function handles two scenarios:
     * - New workflows: Apply ELK auto-layout algorithm to position nodes
     * - Existing workflows: Use saved positions but apply smart fit view
     *
     * ReactFlow needs time to initialize before
     * we can apply viewport changes, hence the delays.
     */
    const onInit: OnInit<VulkanNode, Edge> = useCallback(
        (_reactFlowInstance) => {
            setTimeout(() => {
                smartFitView();
            }, 0);

            // Check if workflow has saved UI positions
            if (
                !workflow.workflow?.ui_metadata ||
                Object.keys(workflow.workflow.ui_metadata).length === 0
            ) {
                // New workflow: Apply automatic layout using ELK algorithm
                const unpositionedNodes: UnlayoutedVulkanNode[] = nodes.map((node) => ({
                    ...node,
                }));

                // ELK calculates optimal node positions
                // considering node connections, hierarchy, and spacing
                getLayoutedNodes(unpositionedNodes, edges).then((layoutedNodes) => {
                    // Create position lookup map for efficient updates
                    const nodesMap = Object.fromEntries(
                        layoutedNodes.map((node) => [node.id, node]),
                    );

                    // Update nodes with calculated positions
                    const newNodes = nodes.map((node) => ({
                        ...node,
                        position: nodesMap[node.id].position, // Apply ELK-calculated position
                    }));

                    setNodes(newNodes);

                    // Wait for DOM updates then apply smart fit view
                    setTimeout(() => {
                        smartFitView();
                    }, 100);
                });
            } else {
                // Existing workflow: Positions already saved, just apply smart fit view
                setTimeout(() => {
                    smartFitView();
                }, 100);
            }
        },
        [workflow, nodes, edges, setNodes, smartFitView],
    );

    /**
     * Handle connection end events for node creation dropdown
     *
     * This creates the "drag to create node" UX:
     * - User drags from a node handle
     * - If they drop on empty space (not on another node), show create menu
     * - Position the menu exactly where they dropped
     * - When they select a node type, create it and connect automatically
     *
     */
    const onConnectEnd = useCallback(
        (event: any, connectionState: any) => {
            // Connection is invalid when dropped on empty space (not on a valid target)
            if (!connectionState.isValid) {
                // Get cursor position - handle mouse events
                const { clientX, clientY } =
                    "changedTouches" in event ? event.changedTouches[0] : event;

                // Store position for dropdown placement (screen coordinates, not flow coordinates)
                setDropdownPosition({ x: clientX, y: clientY });

                // Show dropdown and remember which handle initiated the connection
                toggleDropdown(connectionState.fromHandle);
            }
        },
        [toggleDropdown],
    );

    /**
     * Add a new node and connect it to the current connection
     *
     * Process:
     * - Convert screen coordinates to flow coordinates (accounts for zoom)
     * - Create new node of specified type at that position
     * - Automatically connect it to the handle that initiated the drag
     * - Use null for targetHandle to let ReactFlow auto-select the best input
     *
     * screenToFlowPosition handles the math for
     * converting mouse coordinates to flow canvas coordinates
     */
    function onAddNode(type: string) {
        // Convert screen coordinates (where user dropped) to flow coordinates
        const position = screenToFlowPosition({
            x: dropdownPosition.x,
            y: dropdownPosition.y,
        });

        // Create the new node at calculated position
        const nodeId = addNodeByType(type as any, position);

        // Auto-connect if we have both a new node and a source handle
        if (nodeId && connectingHandle) {
            onConnect({
                source: connectingHandle.nodeId, // Source node that started the drag
                target: nodeId, // Newly created target node
                sourceHandle: connectingHandle.id, // Specific output handle
                targetHandle: null, // Let ReactFlow pick best input
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
     * Apply automatic ELK layout algorithm to reorganize all nodes
     *
     * When workflow becomes messy or nodes overlap
     *
     * Process:
     * - Convert current nodes to "unlayouted" format (preserves data, removes positions)
     * - Send to ELK algorithm with current edges for context
     * - ELK calculates optimal positions considering:
     *    - Node connections and data flow
     *    - Hierarchical relationships
     *    - Minimal edge crossings
     *    - Reasonable spacing
     * - Apply calculated positions back to nodes
     */
    const autoLayoutNodes = useCallback(async () => {
        // Prepare nodes for ELK (remove position data but keep everything else)
        const unpositionedNodes: UnlayoutedVulkanNode[] = nodes.map((node) => ({
            ...node,
        }));

        try {
            // Run ELK layout algorithm
            const layoutedNodes = await getLayoutedNodes(unpositionedNodes, edges);

            // Create efficient lookup map for position updates
            const nodesMap = Object.fromEntries(layoutedNodes.map((node) => [node.id, node]));

            // Apply ELK-calculated positions to existing nodes
            const newNodes = nodes.map((node) => ({
                ...node,
                position: nodesMap[node.id].position, // ELK-optimized position
            }));

            setNodes(newNodes);
        } catch (error) {
            // Don't break the UI if layout fails - just log and continue
            console.error("Error applying auto-layout:", error);
        }
    }, [nodes, edges, setNodes]);

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

    return (
        <div className="w-full h-full relative">
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
                <Controls
                    showZoom={false}
                    showInteractive={false}
                    showFitView={false}
                    orientation="horizontal"
                >
                    <ControlButton onClick={smartFitView} title="Smart Fit View">
                        <ToolbarIcon icon={FocusIcon} />
                    </ControlButton>
                    <ControlButton
                        onClick={toggleAllNodesCollapsed}
                        title={areAllNodesCollapsed ? "Expand All" : "Collapse All"}
                    >
                        {areAllNodesCollapsed ? (
                            <ToolbarIcon icon={ChevronDownIcon} />
                        ) : (
                            <ToolbarIcon icon={ChevronUpIcon} />
                        )}
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
