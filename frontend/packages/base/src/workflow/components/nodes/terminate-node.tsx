"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { XIcon } from "lucide-react";
import { type NodeChange } from "@xyflow/react";

import {
    Input,
    Button,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@vulkanlabs/base/ui";

import { useWorkflowStore } from "@/workflow/store";
import { TerminateWorkflowNode } from "./base";
import type { VulkanNodeProps, VulkanNode } from "@/workflow/types/workflow";
import type { NodeDependency, TerminateNodeMetadata } from "@/workflow/types/nodes";

// Define the structure for a metadata mapping row
type MetadataMapping = {
    field: string;
    nodeId: string;
};

/**
 * Terminate node component - ends workflow execution
 */
export function TerminateNode({ id, data, selected, height, width }: VulkanNodeProps) {
    const { updateNodeData, onNodesChange, nodes } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            onNodesChange: state.onNodesChange,
            nodes: state.nodes, // Get all nodes
        })),
    );

    // Local state to manage the metadata mapping rows
    const [metadataMappings, setMetadataMappings] = useState<MetadataMapping[]>([]);

    // Initialize local state from node data
    useEffect(() => {
        // Cast metadata to the specific type for better type checking
        const nodeMetadata = data.metadata as TerminateNodeMetadata | undefined;
        const metadata = nodeMetadata?.return_metadata;

        if (metadata && typeof metadata === "object" && !Array.isArray(metadata)) {
            const initialMappings: MetadataMapping[] = Object.entries(
                metadata as { [key: string]: NodeDependency },
            ).map(([field, dependency]) => ({
                field: field,
                nodeId: dependency.node, // Map 'node' from NodeDependency to 'nodeId'
            }));
            setMetadataMappings(initialMappings);
        } else {
            setMetadataMappings([]); // Initialize as empty if data is missing or not an object
        }
    }, [id, data]);

    // Filter available nodes for selection (exclude the current terminate node)
    const availableNodes = nodes.filter((node) => node.id !== id);

    const setReturnStatus = useCallback(
        (status: string) => {
            updateNodeData(id, {
                ...data,
                metadata: { ...data.metadata, return_status: status },
            });
        },
        [id, data, updateNodeData],
    );

    // Function to update the node data with the current mappings
    const updateReturnMetadata = useCallback(
        (updatedMappings: MetadataMapping[]) => {
            // Convert the array back to the object format { [key: string]: NodeDependency }
            const metadataObject: { [key: string]: NodeDependency } = updatedMappings.reduce(
                (acc, mapping) => {
                    if (mapping.field && mapping.nodeId) {
                        acc[mapping.field] = { node: mapping.nodeId }; // Create NodeDependency object
                    }
                    return acc;
                },
                {} as { [key: string]: NodeDependency },
            );

            updateNodeData(id, {
                ...data,
                metadata: { ...data.metadata, return_metadata: metadataObject },
            });
        },
        [id, data, updateNodeData],
    );

    const handleAddRow = () => {
        // Create a new array with the existing mappings plus a new empty row
        const newMappings = [
            ...metadataMappings,
            { field: " ", nodeId: availableNodes[0]?.id || "" },
        ];
        setMetadataMappings(newMappings);
        updateReturnMetadata(newMappings); // Update node data immediately
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
    };

    const handleUpdateRow = (index: number, field: keyof MetadataMapping, value: string) => {
        const newMappings = metadataMappings.map((row, i) =>
            i === index ? { ...row, [field]: value } : row,
        );
        setMetadataMappings(newMappings);
        updateReturnMetadata(newMappings); // Update node data immediately
    };

    const handleRemoveRow = (index: number) => {
        const newMappings = metadataMappings.filter((_, i) => i !== index);
        setMetadataMappings(newMappings);
        updateReturnMetadata(newMappings); // Update node data immediately
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
    };

    const returnStatus = (data.metadata as any)?.return_status || "";

    return (
        <TerminateWorkflowNode id={id} selected={selected} data={data} width={width}>
            <div className="flex flex-col p-2 w-full h-fit">
                <div className="flex flex-col gap-1 space-y-2 p-3 h-full">
                    <div className="flex flex-col gap-2">
                        <span>Return status:</span>
                        <div className="nodrag" onMouseDown={(e) => e.stopPropagation()}>
                            <Input
                                type="text"
                                value={returnStatus}
                                onChange={(e) => setReturnStatus(e.target.value)}
                            />
                        </div>
                    </div>
                    <div className="flex flex-col gap-2 flex-grow min-h-0">
                        <span>Return metadata:</span>
                        <div className="nodrag flex flex-col gap-2 h-full overflow-y-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Field</TableHead>
                                        <TableHead>Source Node</TableHead>
                                        <TableHead className="w-[40px]"></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {metadataMappings.map((row, index) => (
                                        <TableRow key={index}>
                                            <TableCell>
                                                <Input
                                                    type="text"
                                                    value={row.field}
                                                    onChange={(e) =>
                                                        handleUpdateRow(
                                                            index,
                                                            "field",
                                                            e.target.value,
                                                        )
                                                    }
                                                    placeholder="Field Name"
                                                    className="h-8"
                                                    onMouseDown={(e) => e.stopPropagation()}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <Select
                                                    value={row.nodeId}
                                                    onValueChange={(value) =>
                                                        handleUpdateRow(index, "nodeId", value)
                                                    }
                                                >
                                                    <SelectTrigger
                                                        className="h-8"
                                                        onMouseDown={(e) => e.stopPropagation()}
                                                    >
                                                        <SelectValue placeholder="Select Node" />
                                                    </SelectTrigger>
                                                    <SelectContent
                                                        onMouseDown={(e) => e.stopPropagation()}
                                                    >
                                                        {availableNodes.map((node) => (
                                                            <SelectItem
                                                                key={node.id}
                                                                value={node.id}
                                                            >
                                                                {node.data.name}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </TableCell>
                                            <TableCell>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8"
                                                    onClick={() => handleRemoveRow(index)}
                                                    onMouseDown={(e) => e.stopPropagation()}
                                                >
                                                    <XIcon className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                            <Button
                                onClick={handleAddRow}
                                variant="outline"
                                size="sm"
                                className="mt-2"
                                onMouseDown={(e) => e.stopPropagation()}
                            >
                                Add Metadata Field
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </TerminateWorkflowNode>
    );
}
