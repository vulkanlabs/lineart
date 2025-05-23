import { useCallback, useState, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { NodeProps } from "@xyflow/react";

import { AssetCombobox, AssetOption } from "@/components/combobox";

import { useWorkflowStore } from "../store";
import { StandardWorkflowNode } from "./base";
import { VulkanNode } from "../types";
import { fetchDataSources } from "@/lib/api";

export function DataInputNode({ id, data, selected, height, width }: NodeProps<VulkanNode>) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const [isLoading, setIsLoading] = useState(false);
    const [dataSources, setDataSources] = useState<AssetOption[]>([]);
    const [selectedDataSource, setSelectedDataSource] = useState(data.metadata?.data_source || "");

    // Fetch data sources when component mounts
    useEffect(() => {
        async function fetchFn() {
            setIsLoading(true);
            try {
                const data = await fetchDataSources().catch((error) => {
                    console.error("Error fetching data sources:", error);
                    return [];
                });
                setDataSources(
                    data.map((source: any) => ({
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
            updateNodeData(id, { ...data, metadata: { data_source: value } });
        },
        [id, data, updateNodeData],
    );

    return (
        <StandardWorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            <div className="flex flex-col gap-1 space-y-2 p-3">
                <span className="nodrag text-sm font-medium">Data Source:</span>
                <AssetCombobox
                    options={dataSources}
                    value={selectedDataSource}
                    onChange={handleDataSourceChange}
                    placeholder="Select a data source..."
                    searchPlaceholder="Search data sources..."
                    isLoading={isLoading}
                    emptyMessage="No data sources found."
                />
            </div>
        </StandardWorkflowNode>
    );
}
