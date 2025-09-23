"use client";

import React, { useCallback, useState, useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { type NodeChange } from "@xyflow/react";

import { AssetCombobox, AssetOption } from "@/components/combobox";
import { Input } from "@vulkanlabs/base/ui";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@vulkanlabs/base/ui";

import { useWorkflowStore } from "@/workflow/store";
import { useWorkflowData } from "@/workflow/context";
import { StandardWorkflowNode } from "./base";
import type { VulkanNodeProps, VulkanNode } from "@/workflow/types/workflow";

/**
 * Data input node component - handles external data sources
 */
export function DataInputNode({ id, data, selected, height, width }: VulkanNodeProps) {
    const { updateNodeData, onNodesChange } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            onNodesChange: state.onNodesChange,
        })),
    );

    // Get data sources from WorkflowDataProvider
    const { dataSources, isDataSourcesLoading, dataSourcesError } = useWorkflowData();

    const nodeData = data as VulkanNode["data"];

    const [selectedDataSource, setSelectedDataSource] = useState(
        nodeData.metadata?.data_source || "",
    );
    const [dataSourceParams, setDataSourceParams] = useState(nodeData.metadata?.parameters || {});

    // Transform data sources into lookup map and AssetOption format
    const dataSourcesMap = useMemo<AssetOption[]>(() => {
        return dataSources.map((source) => ({
            value: source.name,
            label: source.name || source.data_source_id,
        }));
    }, [dataSources]);

    const dataSourcesLookup = useMemo(() => {
        return dataSources.reduce(
            (acc, source) => {
                acc[source.name] = source;
                return acc;
            },
            {} as Record<string, (typeof dataSources)[0]>,
        );
    }, [dataSources]);

    // Helper functions to convert between user format and API format
    const toUserFormat = (value: string): string => {
        if (!value) return "";
        // Remove {{ }} wrapper if present
        return value.replace(/^\{\{(.+)\}\}$/, "$1").trim();
    };

    const toApiFormat = (value: string): string => {
        if (!value) return "";
        // Add {{ }} wrapper if not already present
        return value.startsWith("{{") && value.endsWith("}}") ? value : `{{${value}}}`;
    };

    const handleDataSourceChange = useCallback(
        (value: string) => {
            setSelectedDataSource(value);
            const selectedSource = dataSourcesLookup[value];
            if (selectedSource) {
                const emptyParameters = (selectedSource.runtime_params ?? []).reduce(
                    (acc, param) => ({
                        ...acc,
                        [param]: "",
                    }),
                    {},
                );
                setDataSourceParams(emptyParameters);
                onNodesChange?.([
                    {
                        id: id,
                        type: "dimensions",
                        resizing: true,
                        setAttributes: true,
                        dimensions: {
                            width: width,
                            height: 0,
                        },
                    },
                ] as NodeChange<VulkanNode>[]);
                updateNodeData(id, {
                    ...nodeData,
                    metadata: { data_source: value, parameters: emptyParameters },
                });
            }
        },
        [id, nodeData, width, dataSourcesLookup, onNodesChange, updateNodeData],
    );

    const handleUpdateParam = useCallback(
        (paramName: string, userValue: string) => {
            const apiValue = toApiFormat(userValue);
            const updatedParams = {
                ...dataSourceParams,
                [paramName]: apiValue,
            };
            setDataSourceParams(updatedParams);
            updateNodeData(id, {
                ...nodeData,
                metadata: { ...nodeData.metadata, parameters: updatedParams },
            });
        },
        [id, nodeData, dataSourceParams, updateNodeData],
    );

    return (
        <StandardWorkflowNode id={id} selected={selected} data={nodeData} width={width}>
            <div className="flex flex-col p-3 w-full h-fit">
                <div className="flex flex-col gap-2">
                    <span className="nodrag text-sm font-medium">Data Source:</span>
                    {dataSourcesError ? (
                        <div className="text-sm text-red-600 p-2 bg-red-50 rounded">
                            Error loading data sources: {dataSourcesError}
                        </div>
                    ) : (
                        <AssetCombobox
                            options={dataSourcesMap}
                            value={selectedDataSource}
                            onChange={handleDataSourceChange}
                            placeholder="Select a data source..."
                            searchPlaceholder="Search data sources..."
                            isLoading={isDataSourcesLoading}
                            emptyMessage={
                                isDataSourcesLoading
                                    ? "Loading data sources..."
                                    : "No data sources found."
                            }
                        />
                    )}
                </div>
                <div className="flex flex-col gap-2 mt-4">
                    <span className="nodrag text-sm font-medium">Configuration:</span>
                    <div className="nodrag flex flex-col gap-2 h-full overflow-y-auto">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Parameter</TableHead>
                                    <TableHead>Value</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {Object.entries(dataSourceParams).map(([paramName, value]) => (
                                    <TableRow key={paramName}>
                                        <TableCell>
                                            <span className="text-sm font-medium">{paramName}</span>
                                        </TableCell>
                                        <TableCell>
                                            <Input
                                                type="text"
                                                value={toUserFormat(String(value || ""))}
                                                onChange={(e) =>
                                                    handleUpdateParam(paramName, e.target.value)
                                                }
                                                placeholder="e.g., variable.key"
                                                className="h-8"
                                                onMouseDown={(e) => e.stopPropagation()}
                                            />
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>
                </div>
            </div>
        </StandardWorkflowNode>
    );
}
