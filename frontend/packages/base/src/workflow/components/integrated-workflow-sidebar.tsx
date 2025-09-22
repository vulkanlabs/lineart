"use client";

import React, { useCallback, useState } from "react";
import { useShallow } from "zustand/react/shallow";
import {
    X,
    Code2,
    Settings,
    Network,
    Play,
    ChevronDown,
    ChevronRight,
    Copy,
    Info,
} from "lucide-react";
import Editor from "@monaco-editor/react";

import { useWorkflowStore } from "@/workflow/store";
import { Button } from "@vulkanlabs/base/ui";
import { iconMapping } from "@/workflow/icons";
import { nodesConfig } from "@/workflow/utils/nodes";

// Constants
const SIDEBAR_STORAGE_KEY = "workflow.sidebar.expandedSections";
const DEFAULT_EXPANDED_SECTIONS = ["basic", "connections"];
const DEFAULT_PYTHON_TEMPLATE = `def transform(data):
    # Your transformation logic here
    return data`;

const MONACO_OPTIONS = {
    minimap: { enabled: false },
    automaticLayout: true,
    lineNumbers: "on" as const,
    roundedSelection: false,
    scrollBeyondLastLine: false,
    fontSize: 14,
    fontFamily: 'Monaco, "SF Mono", "JetBrains Mono", Consolas, monospace',
    tabSize: 4,
    wordWrap: "bounded" as const,
    folding: true,
    bracketPairColorization: { enabled: true },
    padding: { top: 20, bottom: 20 },
    renderLineHighlight: "gutter" as const,
    contextmenu: true,
    quickSuggestions: true,
    suggestOnTriggerCharacters: true,
    acceptSuggestionOnEnter: "on" as const,
    tabCompletion: "on" as const,
    wordBasedSuggestions: "currentDocument" as const,
    theme: "vs-dark",
};

/**
 * Custom hook for managing expandable sections
 */
function useExpandableSections(storageKey: string, defaultSections: string[]) {
    const [expandedSections, setExpandedSections] = useState<Set<string>>(() => {
        try {
            const saved = localStorage.getItem(storageKey);
            return saved ? new Set(JSON.parse(saved)) : new Set(defaultSections);
        } catch (e) {
            return new Set(defaultSections);
        }
    });

    const toggleSection = useCallback(
        (section: string) => {
            const newExpanded = new Set(expandedSections);
            if (newExpanded.has(section)) {
                newExpanded.delete(section);
            } else {
                newExpanded.add(section);
            }

            setExpandedSections(newExpanded);
            localStorage.setItem(storageKey, JSON.stringify([...newExpanded]));
        },
        [expandedSections, storageKey],
    );

    return { expandedSections, toggleSection };
}
function formatDependencyOutput(dependency: any, sourceNodeType: string): string {
    if (
        sourceNodeType === "BRANCH" &&
        (!dependency.output || dependency.output === "__DEFAULT__")
    ) {
        return "default";
    }
    return dependency.output || "output";
}

/**
 * Get node type label for display
 */
function getNodeTypeLabel(type: string): string {
    return nodesConfig[type as keyof typeof nodesConfig]?.name || type;
}

/**
 * Utility to render collapsible section header
 */
function CollapsibleSectionHeader({
    icon: IconComponent,
    title,
    badge,
    isExpanded,
    onClick,
}: {
    icon: React.ComponentType<{ size?: number; className?: string }>;
    title: string;
    badge?: number;
    isExpanded: boolean;
    onClick: () => void;
}) {
    return (
        <button
            onClick={onClick}
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
            <div className="flex items-center gap-3">
                <IconComponent size={18} className="text-gray-600" />
                <h3 className="font-medium text-gray-900">{title}</h3>
                {badge !== undefined && badge > 0 && (
                    <span className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full font-medium">
                        {badge}
                    </span>
                )}
            </div>
            {isExpanded ? (
                <ChevronDown size={16} className="text-gray-400" />
            ) : (
                <ChevronRight size={16} className="text-gray-400" />
            )}
        </button>
    );
}

type SidebarTab = "code-editor" | "properties";

interface TabConfig {
    id: SidebarTab;
    label: string;
    icon: React.ComponentType<{ size?: number; className?: string }>;
    description: string;
}

export function IntegratedWorkflowSidebar() {
    const { sidebar, nodes, closeSidebar, setSidebarTab } = useWorkflowStore(
        useShallow((state) => ({
            sidebar: state.sidebar,
            nodes: state.nodes,
            closeSidebar: state.closeSidebar,
            setSidebarTab: state.setSidebarTab,
        })),
    );

    if (!sidebar.isOpen || !sidebar.selectedNodeId) return null;

    const selectedNode = nodes.find((node) => node.id === sidebar.selectedNodeId);
    if (!selectedNode) return null;

    const tabs: TabConfig[] = [
        {
            id: "code-editor",
            label: "Editor",
            icon: Code2,
            description: "Edit transformation code",
        },
        {
            id: "properties",
            label: "Settings",
            icon: Settings,
            description: "Node configuration and connections",
        },
    ];

    const NodeIcon = iconMapping[selectedNode.type as keyof typeof iconMapping] || Code2;

    return (
        <div className="h-full w-full bg-white flex flex-col shadow-xl border-l border-gray-300">
            <div className="px-6 py-4 border-b border-gray-200 bg-white">
                <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start gap-3">
                        <NodeIcon size={18} className="text-gray-600 mt-1" />
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 leading-tight">
                                {selectedNode.data.name || "Transform Node"}
                            </h2>
                            <p className="text-sm text-gray-500">
                                {getNodeTypeLabel(selectedNode.type)} Node
                            </p>
                        </div>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={closeSidebar}
                        className="p-2 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-gray-600 mt-0.5"
                    >
                        <X size={18} />
                    </Button>
                </div>

                <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                    {tabs.map((tab) => {
                        const IconComponent = tab.icon;
                        const isActive = sidebar.activeTab === tab.id;

                        return (
                            <button
                                key={tab.id}
                                onClick={() => setSidebarTab(tab.id)}
                                className={`
                                    flex-1 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium 
                                    rounded-md transition-all duration-200
                                    ${
                                        isActive
                                            ? "bg-white text-gray-900 shadow-sm"
                                            : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                                    }
                                `}
                                title={tab.description}
                            >
                                <IconComponent size={16} />
                                <span>{tab.label}</span>
                            </button>
                        );
                    })}
                </div>
            </div>

            <div className="flex-1 overflow-hidden">
                {sidebar.activeTab === "code-editor" && (
                    <ModernCodeEditor nodeId={sidebar.selectedNodeId} selectedNode={selectedNode} />
                )}
                {sidebar.activeTab === "properties" && (
                    <ModernPropertiesPanel
                        nodeId={sidebar.selectedNodeId}
                        selectedNode={selectedNode}
                    />
                )}
            </div>
        </div>
    );
}

function ModernCodeEditor({ nodeId, selectedNode }: { nodeId: string; selectedNode: any }) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const sourceCode = selectedNode.data.metadata?.source_code || "";

    const setSourceCode = useCallback(
        (code: string | undefined) => {
            updateNodeData(nodeId, {
                ...selectedNode.data,
                metadata: {
                    ...selectedNode.data.metadata,
                    source_code: code || "",
                },
            });
        },
        [nodeId, selectedNode.data, updateNodeData],
    );

    if (selectedNode.type !== "TRANSFORM") {
        return (
            <div className="flex items-center justify-center h-full p-8">
                <div className="text-center">
                    <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
                        <Code2 size={24} className="text-gray-400" />
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Code Editor</h3>
                    <p className="text-gray-500 max-w-sm">
                        Code editing is available for Transform nodes. This node type doesn't
                        support custom code.
                    </p>
                </div>
            </div>
        );
    }

    const editorValue = sourceCode || DEFAULT_PYTHON_TEMPLATE;

    return (
        <div className="h-full flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-gray-900">Python Code</h3>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigator.clipboard.writeText(editorValue)}
                            className="text-gray-600 hover:text-gray-900"
                        >
                            <Copy size={14} />
                        </Button>
                        <Button size="sm" className="bg-gray-900 hover:bg-gray-800 text-white px-4">
                            <Play size={14} className="mr-1.5" />
                            Run
                        </Button>
                    </div>
                </div>
            </div>

            <div className="flex-1 relative">
                <Editor
                    height="100%"
                    language="python"
                    value={editorValue}
                    onChange={(value) => setSourceCode(value)}
                    theme="vs-dark"
                    options={MONACO_OPTIONS}
                />
            </div>
        </div>
    );
}

function ModernPropertiesPanel({ nodeId, selectedNode }: { nodeId: string; selectedNode: any }) {
    const { expandedSections, toggleSection } = useExpandableSections(
        SIDEBAR_STORAGE_KEY,
        DEFAULT_EXPANDED_SECTIONS,
    );

    const { updateNodeData, nodes } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            nodes: state.nodes,
        })),
    );

    const incomingEdges = selectedNode.data.incomingEdges || {};

    const handleNameChange = (name: string) => {
        updateNodeData(nodeId, { ...selectedNode.data, name });
    };

    const getConnectedNodeType = (nodeName: string) => {
        const connectedNode = nodes.find((node) => node.data.name === nodeName);
        return connectedNode?.type || "Unknown";
    };

    return (
        <div className="h-full overflow-auto">
            <div className="border-b border-gray-200">
                <CollapsibleSectionHeader
                    icon={Settings}
                    title="Configuration"
                    isExpanded={expandedSections.has("basic")}
                    onClick={() => toggleSection("basic")}
                />

                {expandedSections.has("basic") && (
                    <div className="px-6 pb-6 space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Node Name
                            </label>
                            <input
                                type="text"
                                value={selectedNode.data.name || ""}
                                onChange={(e) => handleNameChange(e.target.value)}
                                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors"
                                placeholder="Enter a descriptive name..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Description
                            </label>
                            <textarea
                                value={selectedNode.data.description || ""}
                                onChange={(e) =>
                                    updateNodeData(nodeId, {
                                        ...selectedNode.data,
                                        description: e.target.value,
                                    })
                                }
                                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm h-24 resize-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 transition-colors"
                                placeholder="Describe what this node does..."
                            />
                        </div>
                    </div>
                )}
            </div>

            <div className="border-b border-gray-200">
                <CollapsibleSectionHeader
                    icon={Network}
                    title="Connections"
                    badge={Object.keys(incomingEdges).length}
                    isExpanded={expandedSections.has("connections")}
                    onClick={() => toggleSection("connections")}
                />

                {expandedSections.has("connections") && (
                    <div className="px-6 pb-6">
                        {Object.keys(incomingEdges).length === 0 ? (
                            <div className="text-center py-8">
                                <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
                                    <Network size={20} className="text-gray-400" />
                                </div>
                                <h4 className="font-medium text-gray-900 mb-1">No Connections</h4>
                                <p className="text-sm text-gray-500">
                                    Connect other nodes to provide data inputs
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {Object.entries(incomingEdges).map(([edgeId, edgeConfig]) => {
                                    const { key, dependency } = edgeConfig as {
                                        key: string;
                                        dependency: any;
                                    };
                                    const nodeType = getConnectedNodeType(dependency.node);
                                    const formattedOutput = formatDependencyOutput(
                                        dependency,
                                        nodeType,
                                    );

                                    return (
                                        <div
                                            key={edgeId}
                                            className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors bg-white"
                                        >
                                            <div className="flex items-start justify-between mb-3">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                                    <div>
                                                        <div className="font-medium text-gray-900">
                                                            {key}
                                                        </div>
                                                        <div className="text-sm text-gray-500">
                                                            Input variable
                                                        </div>
                                                    </div>
                                                </div>
                                                <span className="bg-gray-100 text-gray-700 text-xs px-2.5 py-1 rounded-md font-medium">
                                                    {getNodeTypeLabel(nodeType)}
                                                </span>
                                            </div>

                                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                                <span>Source:</span>
                                                <span className="font-medium text-gray-900">
                                                    {dependency.node}
                                                </span>
                                                <ChevronRight size={14} className="text-gray-400" />
                                                <span className="text-gray-700 font-medium">
                                                    {formattedOutput}
                                                </span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}
            </div>

            <div>
                <CollapsibleSectionHeader
                    icon={Info}
                    title="Information"
                    isExpanded={expandedSections.has("info")}
                    onClick={() => toggleSection("info")}
                />

                {expandedSections.has("info") && (
                    <div className="px-6 pb-6 space-y-4">
                        <div className="grid grid-cols-1 gap-4">
                            <div className="bg-gray-50 rounded-lg p-4">
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <span className="text-gray-500 block">Node Type</span>
                                        <div className="font-medium text-gray-900 mt-1">
                                            {getNodeTypeLabel(selectedNode.type)}
                                        </div>
                                    </div>
                                    <div className="col-span-2">
                                        <span className="text-gray-500 block">Node ID</span>
                                        <div className="font-mono text-xs text-gray-700 break-all mt-1 bg-white px-2 py-1 rounded border">
                                            {selectedNode.id}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
