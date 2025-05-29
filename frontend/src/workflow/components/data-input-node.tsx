import { useCallback, useState, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { NodeProps, type NodeChange } from "@xyflow/react";

import { DataSource } from "@vulkan-server/DataSource";
import { AssetCombobox, AssetOption } from "@/components/combobox";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { fetchDataSources } from "@/lib/api";

import { useWorkflowStore } from "../store";
import { StandardWorkflowNode } from "./base";
import { VulkanNode } from "../types";

export function DataInputNode({ id, data, selected, height, width }: NodeProps<VulkanNode>) {
    const { updateNodeData, onNodesChange } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            onNodesChange: state.onNodesChange,
        })),
    );

    const [isLoading, setIsLoading] = useState(false);
    const [dataSources, setDataSources] = useState<Record<string, DataSource | undefined>>({});
    const [dataSourcesMap, setDataSourcesMap] = useState<AssetOption[]>([]);
    const [selectedDataSource, setSelectedDataSource] = useState(data.metadata?.data_source || "");
    const [dataSourceParams, setDataSourceParams] = useState(data.metadata?.parameters || {});

    // Fetch data sources when component mounts
    useEffect(() => {
        async function fetchFn() {
            setIsLoading(true);
            try {
                const sources: DataSource[] = await fetchDataSources().catch((error) => {
                    console.error("Error fetching data sources:", error);
                    return [];
                });
                setDataSources(
                    sources.reduce((acc: Record<string, DataSource>, source: DataSource) => {
                        acc[source.data_source_id] = source;
                        return acc;
                    }, {}),
                );
                setDataSourcesMap(
                    sources.map((source: any) => ({
                        value: source.data_source_id,
                        label: source.name || source.data_source_id,
                    })),
                );
            } catch (error) {
                console.error("Error fetching data sources:", error);
                // Handle error appropriately
            } finally {
                setIsLoading(false);
            }
        }

        fetchFn();
    }, []);

    const handleDataSourceChange = useCallback(
        (value: string) => {
            setSelectedDataSource(value);
            const emptyParameters = dataSources[value].runtime_params.reduce(
                (acc, param) => ({
                    ...acc,
                    [param]: "",
                }),
                {},
            );
            setDataSourceParams(emptyParameters);
            onNodesChange([
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
                ...data,
                metadata: { data_source: value, parameters: emptyParameters },
            });
        },
        [id, data, width, dataSources, onNodesChange, updateNodeData],
    );

    const handleUpdateParam = useCallback(
        (key: string, field: "variable" | "key", value: string) => {
            const updatedParams = {
                ...dataSourceParams,
                [key]: {
                    ...dataSourceParams[key],
                    [field]: value,
                },
            };
            setDataSourceParams(updatedParams);
            updateNodeData(id, {
                ...data,
                metadata: { ...data.metadata, parameters: updatedParams },
            });
        },
        [id, data, dataSourceParams, updateNodeData],
    );

    return (
        <StandardWorkflowNode id={id} selected={selected} data={data} width={width}>
            <div className="flex flex-col p-2 w-full h-fit">
                <div className="flex flex-col gap-1 space-y-2 p-3">
                    <span className="nodrag text-sm font-medium">Data Source:</span>
                    <AssetCombobox
                        options={dataSourcesMap}
                        value={selectedDataSource}
                        onChange={handleDataSourceChange}
                        placeholder="Select a data source..."
                        searchPlaceholder="Search data sources..."
                        isLoading={isLoading}
                        emptyMessage="No data sources found."
                    />
                </div>
                <div className="flex flex-col gap-1 space-y-2 p-3">
                    <span className="nodrag text-sm font-medium">Configuration:</span>
                    <div className="nodrag flex flex-col gap-2 h-full overflow-y-auto">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Parameter</TableHead>
                                    <TableHead>Variable</TableHead>
                                    <TableHead>Key</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {Object.entries(dataSourceParams).map(
                                    ([key, value]: [string, any]) => (
                                        <TableRow key={key}>
                                            <TableCell>
                                                <span className="text-sm font-medium">{key}</span>
                                            </TableCell>
                                            <TableCell>
                                                <Input
                                                    type="text"
                                                    value={value.variable || ""}
                                                    onChange={(e) =>
                                                        handleUpdateParam(
                                                            key,
                                                            "variable",
                                                            e.target.value,
                                                        )
                                                    }
                                                    placeholder="variable"
                                                    className="h-8"
                                                    onMouseDown={(e) => e.stopPropagation()}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <Input
                                                    type="text"
                                                    value={value.key || ""}
                                                    onChange={(e) =>
                                                        handleUpdateParam(
                                                            key,
                                                            "key",
                                                            e.target.value,
                                                        )
                                                    }
                                                    placeholder="key"
                                                    className="h-8"
                                                    onMouseDown={(e) => e.stopPropagation()}
                                                />
                                            </TableCell>
                                        </TableRow>
                                    ),
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </div>
            </div>
        </StandardWorkflowNode>
    );
}
