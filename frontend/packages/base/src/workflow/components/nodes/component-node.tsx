"use client";

import React, { useCallback, useState, useMemo, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { Link, Puzzle } from "lucide-react";

import { AssetCombobox, AssetOption } from "@/components/combobox";
import { Input } from "@vulkanlabs/base/ui";

import { useWorkflowStore } from "@/workflow/store";
import { useWorkflowData } from "@/workflow/context";
import { StandardWorkflowNode } from "./base";
import type { VulkanNodeProps } from "@/workflow/types/workflow";
import { Component, WorkflowStatus } from "@vulkanlabs/client-open";

/**
 * Component details display component
 */
interface ComponentDetailsProps {
    component: Component;
}

function ComponentDetails({ component }: ComponentDetailsProps) {
    return (
        <div
            className="mt-4 p-3 bg-gray-50 rounded-lg"
            onDoubleClick={() => {
                window.open(`/components/${component.component_id}`, "_blank");
            }}
        >
            <div className="flex items-center gap-3 mb-2">
                {component.icon ? (
                    <img
                        src={component.icon}
                        alt="Component icon"
                        className="h-8 w-8 object-contain rounded"
                    />
                ) : (
                    <div className="h-8 w-8 bg-gray-200 rounded flex items-center justify-center">
                        <Puzzle className="h-4 w-4 text-gray-500" />
                    </div>
                )}
                <div className="text-sm font-medium text-gray-900">{component.name}</div>
            </div>
            {component.description && (
                <div className="text-sm text-gray-600 mb-2">{component.description}</div>
            )}
        </div>
    );
}

/**
 * Component node component - executes sub-components within workflow
 */
export function ComponentNode({ id, data, selected, height, width }: VulkanNodeProps) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    // Get component data from WorkflowDataProvider
    const { components, isComponentsLoading, componentsError } = useWorkflowData();

    const setComponentID = useCallback(
        (component_id: string) => {
            updateNodeData(id, { ...(data || {}), metadata: { component_id: component_id } });
        },
        [id, data, updateNodeData],
    );

    const [selectedComponent, setSelectedComponent] = useState(data.metadata?.component_id || "");

    // Transform components into AssetOption format
    const componentOptions = useMemo<AssetOption[]>(() => {
        return components
            .filter((component) => component.workflow?.status === WorkflowStatus.Valid)
            .map((component) => ({
                value: component.component_id,
                label: component.name,
                icon: component.icon || undefined,
            }));
    }, [components]);

    // Get selected component details for display
    const selectedComponentDetails = useMemo(() => {
        return components.find((component) => component.component_id === selectedComponent);
    }, [components, selectedComponent]);

    // Get component input fields from workflow spec
    const componentInputFields = useMemo(() => {
        if (!selectedComponentDetails?.workflow?.spec?.nodes) return [];

        const inputNode = selectedComponentDetails.workflow.spec.nodes.find(
            (node) => node.node_type === "INPUT",
        );

        if (!inputNode?.metadata || typeof inputNode.metadata !== "object") return [];

        const metadata = inputNode.metadata as any;
        if (!metadata.schema || typeof metadata.schema !== "object") return [];

        return Object.keys(metadata.schema);
    }, [selectedComponentDetails]);

    // Get current field mappings from metadata
    const fieldMappings = data.metadata?.field_mappings || {};

    // Update field mappings
    const updateFieldMapping = useCallback(
        (fieldName: string, value: string) => {
            const newMappings = { ...fieldMappings, [fieldName]: value };
            updateNodeData(id, {
                ...(data || {}),
                metadata: {
                    ...data.metadata,
                    component_id: selectedComponent,
                    field_mappings: newMappings,
                },
            });
        },
        [id, data, fieldMappings, selectedComponent, updateNodeData],
    );

    // Update node icon when component is selected
    // useEffect(() => {
    //     if (selectedComponentDetails?.icon) {
    //         updateNodeData(id, {
    //             ...data,
    //             icon: selectedComponentDetails.icon,
    //         });
    //     }
    // }, [selectedComponentDetails, id, data, updateNodeData]);

    console.log("Input fields", componentInputFields);

    return (
        <StandardWorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            <div className="flex flex-col gap-4 p-4">
                {componentsError ? (
                    <div className="text-sm text-red-600 p-2 bg-red-50 rounded">
                        Error loading components: {componentsError}
                    </div>
                ) : (
                    <AssetCombobox
                        options={componentOptions}
                        value={selectedComponent}
                        onChange={(value: string) => {
                            setSelectedComponent(value);
                            setComponentID(value);
                            updateNodeData(id, {
                                ...(data || {}),
                                metadata: { component_id: value },
                            });
                        }}
                        placeholder="Select a component..."
                        searchPlaceholder="Search components..."
                        isLoading={isComponentsLoading}
                        emptyMessage={
                            isComponentsLoading
                                ? "Loading components..."
                                : "No valid components found."
                        }
                    />
                )}

                {/* Display selected component details */}
                {selectedComponentDetails && (
                    <ComponentDetails component={selectedComponentDetails} />
                )}

                {/* Input field configuration */}
                {componentInputFields.length > 0 && (
                    <div className="mt-4">
                        <span className="text-sm font-medium text-gray-700 mb-3 block">
                            Configure Input Fields:
                        </span>
                        <div className="space-y-3">
                            {componentInputFields.map((fieldName) => (
                                <div key={fieldName} className="flex flex-col gap-1">
                                    <label className="text-xs font-medium text-gray-600">
                                        {fieldName}:
                                    </label>
                                    <Input
                                        value={fieldMappings[fieldName] || ""}
                                        onChange={(e) =>
                                            updateFieldMapping(fieldName, e.target.value)
                                        }
                                        placeholder={`Enter value for ${fieldName}`}
                                        className="text-xs h-8"
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </StandardWorkflowNode>
    );
}
