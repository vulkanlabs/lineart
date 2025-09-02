"use client";

import React, { useState, useRef } from "react";
import { Panel, PanelGroup, ImperativePanelGroupHandle } from "react-resizable-panels";

import type { NodeDefinitionDict, RunData, RunLogs } from "@vulkanlabs/client-open";

import { ResizeHandle } from "../resize-handle";

import { WorkflowFrame } from "./workflow/frame";
import { EdgeLayoutConfig, NodeLayoutConfig, RunNodeLayout } from "./workflow/types";
import { makeGraphElements } from "./workflow/graph";

import { LogsTable } from "./run-logs";
import { WorkflowSidebar } from "./run-sidebar";
import { WorkflowSkeleton, SidebarSkeleton, LogsTableSkeleton, ErrorState } from "./loading-states";

export interface RunPageConfig {
    containerOverflow?: "hidden" | "scroll";
    sidebarOverflow?: "hidden" | "auto";
    tableClass?: "w-full" | "min-w-full";
    enableResponsiveColumns?: boolean;
    isLoading?: boolean;
    error?: string;
}

export function RunPageContent({
    nodes,
    runLogs,
    runData,
    config,
}: {
    nodes: NodeDefinitionDict[];
    runLogs: RunLogs;
    runData: RunData;
    config?: RunPageConfig;
}) {
    const [clickedNode, setClickedNode] = useState(null);
    const {
        containerOverflow = "scroll",
        sidebarOverflow = "auto",
        tableClass = "w-full",
        enableResponsiveColumns = true,
        isLoading = false,
        error,
    } = config || {};

    const [runNodes, edges] = getGraphElements(nodes, runData);

    const containerOverflowClass =
        containerOverflow === "hidden" ? "overflow-hidden" : "overflow-scroll";
    const sidebarOverflowClass = sidebarOverflow === "hidden" ? "overflow-hidden" : "overflow-auto";

    // Default panel sizes
    const DEFAULT_VERTICAL_SIZES = [50, 50];
    const DEFAULT_HORIZONTAL_SIZES = [70, 30];

    // Initialize panel sizes from localStorage or defaults
    const [verticalSizes, setVerticalSizes] = useState<number[]>(() => {
        try {
            const saved = localStorage.getItem("runPage.verticalPanelSizes");
            return saved ? JSON.parse(saved) : DEFAULT_VERTICAL_SIZES;
        } catch (e) {
            console.error("Failed to parse saved vertical panel sizes");
            return DEFAULT_VERTICAL_SIZES;
        }
    });

    const [horizontalSizes, setHorizontalSizes] = useState<number[]>(() => {
        try {
            const saved = localStorage.getItem("runPage.horizontalPanelSizes");
            return saved ? JSON.parse(saved) : DEFAULT_HORIZONTAL_SIZES;
        } catch (e) {
            console.error("Failed to parse saved horizontal panel sizes");
            return DEFAULT_HORIZONTAL_SIZES;
        }
    });

    // Refs for imperative panel control
    const verticalPanelRef = useRef<ImperativePanelGroupHandle>(null);
    const horizontalPanelRef = useRef<ImperativePanelGroupHandle>(null);

    const handleVerticalResize = (sizes: number[]) => {
        setVerticalSizes(sizes);
        localStorage.setItem("runPage.verticalPanelSizes", JSON.stringify(sizes));
    };

    const handleHorizontalResize = (sizes: number[]) => {
        setHorizontalSizes(sizes);
        localStorage.setItem("runPage.horizontalPanelSizes", JSON.stringify(sizes));
    };

    const resetVerticalSizes = () => {
        verticalPanelRef.current?.setLayout(DEFAULT_VERTICAL_SIZES);
        setVerticalSizes(DEFAULT_VERTICAL_SIZES);
        localStorage.setItem("runPage.verticalPanelSizes", JSON.stringify(DEFAULT_VERTICAL_SIZES));
    };

    const resetHorizontalSizes = () => {
        horizontalPanelRef.current?.setLayout(DEFAULT_HORIZONTAL_SIZES);
        setHorizontalSizes(DEFAULT_HORIZONTAL_SIZES);
        localStorage.setItem(
            "runPage.horizontalPanelSizes",
            JSON.stringify(DEFAULT_HORIZONTAL_SIZES),
        );
    };

    // Error state
    if (error) {
        return (
            <div className={`h-full w-full ${containerOverflowClass} bg-gray-50`}>
                <ErrorState
                    title="Failed to Load Run Data"
                    message={error}
                    onRetry={() => window.location.reload()}
                />
            </div>
        );
    }

    // Loading state
    if (isLoading) {
        return (
            <div className={`h-full w-full ${containerOverflowClass} bg-gray-50`}>
                <PanelGroup direction="vertical" className="h-full w-full">
                    <Panel defaultSize={60} minSize={30}>
                        <PanelGroup direction="horizontal" className="h-full w-full">
                            <Panel defaultSize={70} minSize={40}>
                                <WorkflowSkeleton />
                            </Panel>
                            <div className="w-1.5 bg-gray-200" />
                            <Panel defaultSize={30} minSize={20}>
                                <SidebarSkeleton />
                            </Panel>
                        </PanelGroup>
                    </Panel>
                    <div className="h-1.5 bg-gray-200" />
                    <Panel defaultSize={40} minSize={20}>
                        <LogsTableSkeleton />
                    </Panel>
                </PanelGroup>
            </div>
        );
    }

    return (
        <div className={`h-full w-full ${containerOverflowClass} bg-gray-50 relative`}>
            <PanelGroup
                ref={verticalPanelRef}
                direction="vertical"
                onLayout={handleVerticalResize}
                className="h-full w-full"
            >
                <Panel defaultSize={verticalSizes[0]} minSize={30}>
                    <PanelGroup
                        ref={horizontalPanelRef}
                        direction="horizontal"
                        onLayout={handleHorizontalResize}
                        className="h-full w-full"
                    >
                        <Panel defaultSize={horizontalSizes[0]} minSize={40}>
                            <div className="w-full h-full bg-white">
                                <WorkflowFrame
                                    nodes={runNodes}
                                    edges={edges}
                                    onNodeClick={(_: any, node: any) => setClickedNode(node)}
                                    onPaneClick={() => setClickedNode(null)}
                                />
                            </div>
                        </Panel>
                        <ResizeHandle direction="horizontal" onDoubleClick={resetHorizontalSizes} />
                        <Panel defaultSize={horizontalSizes[1]} minSize={20}>
                            <div className={`h-full ${sidebarOverflowClass}`}>
                                <WorkflowSidebar clickedNode={clickedNode} runData={runData} />
                            </div>
                        </Panel>
                    </PanelGroup>
                </Panel>
                <ResizeHandle direction="vertical" onDoubleClick={resetVerticalSizes} />
                <Panel defaultSize={verticalSizes[1]} minSize={20}>
                    <div className="h-full w-full bg-white">
                        <LogsTable
                            runLogs={runLogs}
                            clickedNode={clickedNode}
                            tableClass={tableClass}
                            enableResponsiveColumns={enableResponsiveColumns}
                        />
                    </div>
                </Panel>
            </PanelGroup>
        </div>
    );
}

function getGraphElements(
    nodes: NodeDefinitionDict[],
    runData: RunData,
): [RunNodeLayout[], EdgeLayoutConfig[]] {
    const inputNode: NodeDefinitionDict = {
        name: "input_node",
        node_type: "INPUT",
        dependencies: null,
        metadata: null,
    };
    const allNodes = nodes.length > 0 ? [...nodes, inputNode] : nodes;

    const [nodesToLayout, edges] = makeGraphElements(allNodes);

    const runNodes: RunNodeLayout[] = nodesToLayout.map((node: NodeLayoutConfig) => {
        const runNode = {
            ...node,
            data: {
                ...node.data,
                run: runData.steps[node.id] || null,
            },
        };
        return runNode;
    });
    return [runNodes, edges];
}
