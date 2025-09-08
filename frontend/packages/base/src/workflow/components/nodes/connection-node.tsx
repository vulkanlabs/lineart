"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useShallow } from "zustand/react/shallow";

import {
    Input,
    Label,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
    Textarea,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
    Button,
} from "@vulkanlabs/base/ui";
import { Plus, Trash2, ChevronDown, ChevronRight, Check, X } from "lucide-react";

import { useWorkflowStore } from "@/workflow/store";
import { StandardWorkflowNode } from "./base";
import type { VulkanNodeProps, VulkanNode, VulkanNodeData } from "@/workflow/types/workflow";

interface ConnectionMetadata {
    url?: string;
    method?: string;
    headers?: Record<string, string>;
    params?: Record<string, string>;
    body?: Record<string, string>;
    timeout?: number;
    retry_max_retries?: number;
    response_type?: string;
}

/**
 * Connection node component - manages connections between workflow elements
 */
export function ConnectionNode({ id, data, selected, width }: VulkanNodeProps) {
    const { updateNodeData } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
        })),
    );

    const nodeData = data as VulkanNodeData;
    const metadata: ConnectionMetadata = useMemo(
        () => nodeData.metadata || {},
        [nodeData.metadata],
    );

    const [localMetadata, setLocalMetadata] = useState<ConnectionMetadata>(metadata);
    const [bodyText, setBodyText] = useState<string>(JSON.stringify(metadata.body || {}, null, 2));
    const [isBodyCollapsed, setIsBodyCollapsed] = useState<boolean>(true);
    const [isBodyValid, setIsBodyValid] = useState<boolean>(true);

    // Sync localMetadata when data.metadata changes
    useEffect(() => {
        setLocalMetadata(metadata);
        const newBodyText = JSON.stringify(metadata.body || {}, null, 2);
        setBodyText(newBodyText);
        try {
            JSON.parse(newBodyText);
            setIsBodyValid(true);
        } catch {
            setIsBodyValid(false);
        }
    }, [metadata]);

    const updateMetadata = useCallback(
        (updates: Partial<ConnectionMetadata>) => {
            const newMetadata = { ...localMetadata, ...updates };
            setLocalMetadata(newMetadata);
            updateNodeData(id, {
                ...nodeData,
                metadata: newMetadata,
            });
        },
        [id, nodeData, localMetadata, updateNodeData],
    );

    const addKeyValuePair = useCallback(
        (section: "headers" | "params" | "body") => {
            const newSection = { ...(localMetadata[section] || {}), "": "" };
            updateMetadata({ [section]: newSection });
        },
        [localMetadata, updateMetadata],
    );

    const updateKeyValuePair = useCallback(
        (section: "headers" | "params" | "body", oldKey: string, newKey: string, value: string) => {
            const currentSection = { ...(localMetadata[section] || {}) };
            if (oldKey !== newKey && oldKey in currentSection) {
                delete currentSection[oldKey];
            }
            currentSection[newKey] = value;
            updateMetadata({ [section]: currentSection });
        },
        [localMetadata, updateMetadata],
    );

    const removeKeyValuePair = useCallback(
        (section: "headers" | "params" | "body", key: string) => {
            const currentSection = { ...(localMetadata[section] || {}) };
            delete currentSection[key];
            updateMetadata({ [section]: currentSection });
        },
        [localMetadata, updateMetadata],
    );

    const renderKeyValueSection = (
        title: string,
        section: "headers" | "params" | "body",
        data: Record<string, string>,
    ) => {
        return (
            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">{title}</Label>
                    <Button
                        size="sm"
                        variant="outline"
                        onClick={() => addKeyValuePair(section)}
                        className="h-6 px-2"
                    >
                        <Plus className="h-3 w-3" />
                    </Button>
                </div>
                {data && Object.keys(data).length > 0 && (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-1/3">Key</TableHead>
                                <TableHead className="w-1/2">Value</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {Object.entries(data).map(([key, value], index) => (
                                <TableRow key={index}>
                                    <TableCell>
                                        <div
                                            className="nodrag"
                                            onMouseDown={(e) => e.stopPropagation()}
                                        >
                                            <Input
                                                value={key}
                                                onChange={(e) =>
                                                    updateKeyValuePair(
                                                        section,
                                                        key,
                                                        e.target.value,
                                                        value,
                                                    )
                                                }
                                                placeholder="key"
                                                className="h-8"
                                            />
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div
                                            className="nodrag"
                                            onMouseDown={(e) => e.stopPropagation()}
                                        >
                                            <Input
                                                value={value}
                                                onChange={(e) =>
                                                    updateKeyValuePair(
                                                        section,
                                                        key,
                                                        key,
                                                        e.target.value,
                                                    )
                                                }
                                                placeholder="value"
                                                className="h-8"
                                            />
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => removeKeyValuePair(section, key)}
                                            className="h-6 w-6 p-0"
                                        >
                                            <Trash2 className="h-3 w-3" />
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </div>
        );
    };

    return (
        <StandardWorkflowNode id={id} selected={selected} data={nodeData} width={width}>
            <div className="flex flex-col p-4 w-full h-fit space-y-4">
                <div className="space-y-2">
                    <Label className="text-sm font-medium">URL</Label>
                    <div className="nodrag" onMouseDown={(e) => e.stopPropagation()}>
                        <Input
                            value={localMetadata.url || ""}
                            onChange={(e) => updateMetadata({ url: e.target.value })}
                            placeholder="https://api.example.com/endpoint"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Method</Label>
                        <Select
                            value={localMetadata.method}
                            onValueChange={(value) => updateMetadata({ method: value })}
                        >
                            <SelectTrigger onMouseDown={(e) => e.stopPropagation()}>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="GET">GET</SelectItem>
                                <SelectItem value="POST">POST</SelectItem>
                                <SelectItem value="PUT">PUT</SelectItem>
                                <SelectItem value="DELETE">DELETE</SelectItem>
                                <SelectItem value="PATCH">PATCH</SelectItem>
                                <SelectItem value="HEAD">HEAD</SelectItem>
                                <SelectItem value="OPTIONS">OPTIONS</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Response Type</Label>
                        <Select
                            value={localMetadata.response_type}
                            onValueChange={(value) => updateMetadata({ response_type: value })}
                        >
                            <SelectTrigger onMouseDown={(e) => e.stopPropagation()}>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="JSON">JSON</SelectItem>
                                <SelectItem value="XML">XML</SelectItem>
                                <SelectItem value="CSV">CSV</SelectItem>
                                <SelectItem value="PLAIN_TEXT">Plain Text</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Timeout (seconds)</Label>
                        <div className="nodrag" onMouseDown={(e) => e.stopPropagation()}>
                            <Input
                                type="number"
                                value={localMetadata.timeout || ""}
                                onChange={(e) =>
                                    updateMetadata({
                                        timeout: e.target.value
                                            ? parseInt(e.target.value)
                                            : undefined,
                                    })
                                }
                                placeholder="30"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label className="text-sm font-medium">Max Retries</Label>
                        <div className="nodrag" onMouseDown={(e) => e.stopPropagation()}>
                            <Input
                                type="number"
                                value={localMetadata.retry_max_retries}
                                onChange={(e) =>
                                    updateMetadata({
                                        retry_max_retries: parseInt(e.target.value) || 1,
                                    })
                                }
                                min="0"
                            />
                        </div>
                    </div>
                </div>

                {renderKeyValueSection("Headers", "headers", localMetadata.headers || {})}
                {renderKeyValueSection("Query Parameters", "params", localMetadata.params || {})}

                <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setIsBodyCollapsed(!isBodyCollapsed)}
                            className="p-1 h-auto"
                        >
                            {isBodyCollapsed ? (
                                <ChevronRight className="h-4 w-4" />
                            ) : (
                                <ChevronDown className="h-4 w-4" />
                            )}
                        </Button>
                        <Label className="text-sm font-medium">Request Body (JSON)</Label>
                        <span
                            className={`text-xs ${isBodyValid ? "text-green-500" : "text-red-500"}`}
                        >
                            {isBodyValid ? <Check color="green" /> : <X color="red" />}
                        </span>
                    </div>
                    {!isBodyCollapsed && (
                        <div className="nodrag" onMouseDown={(e) => e.stopPropagation()}>
                            <Textarea
                                value={bodyText}
                                onChange={(e) => {
                                    const newValue = e.target.value;
                                    setBodyText(newValue);
                                    try {
                                        const parsed = JSON.parse(newValue);
                                        updateMetadata({ body: parsed });
                                        setIsBodyValid(true);
                                    } catch {
                                        // Invalid JSON, don't update metadata but keep the text
                                        setIsBodyValid(false);
                                    }
                                }}
                                placeholder="{}"
                                className="min-h-[100px] font-mono text-xs"
                            />
                        </div>
                    )}
                </div>
            </div>
        </StandardWorkflowNode>
    );
}
