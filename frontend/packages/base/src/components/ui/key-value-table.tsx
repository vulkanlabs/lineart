"use client";

import React, { useState, useCallback } from "react";
import { Plus, X } from "lucide-react";
import { Button } from "./button";
import { Input } from "./input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./table";
import { cn } from "../../lib/utils";

export interface KeyValuePair {
    key?: string;
    value?: string;
}

export interface KeyValueTableProps {
    /** Array of key-value pairs */
    value?: KeyValuePair[];
    /** Called when the key-value pairs change */
    onChange?: (pairs: KeyValuePair[]) => void;
    /** Placeholder text for the key input */
    keyPlaceholder?: string;
    /** Placeholder text for the value input */
    valuePlaceholder?: string;
    /** Whether the table is disabled */
    disabled?: boolean;
    /** Custom className for the container */
    className?: string;
    /** Minimum number of rows to show */
    minRows?: number;
    /** Maximum number of rows allowed */
    maxRows?: number;
}

export function KeyValueTable({
    value = [],
    onChange,
    keyPlaceholder = "Key",
    valuePlaceholder = "Value",
    disabled = false,
    className,
}: KeyValueTableProps) {
    const [pairs, setPairs] = useState<KeyValuePair[]>(() => {
        if (value == null || value.length === 0) {
            return [];
        }
        return value.map((pair) => ({ key: pair.key || "", value: pair.value || "" }));
    });

    const updatePairs = useCallback(
        (newPairs: KeyValuePair[]) => {
            setPairs(newPairs);
            onChange?.(
                newPairs.filter(
                    (pair) => (pair.key || "").trim() !== "" || (pair.value || "").trim() !== "",
                ),
            );
        },
        [onChange],
    );

    const handleKeyChange = useCallback(
        (index: number, newKey: string) => {
            const newPairs = [...pairs];
            newPairs[index] = { ...newPairs[index], key: newKey };
            updatePairs(newPairs);
        },
        [pairs, updatePairs],
    );

    const handleValueChange = useCallback(
        (index: number, newValue: string) => {
            const newPairs = [...pairs];
            newPairs[index] = { ...newPairs[index], value: newValue };
            updatePairs(newPairs);
        },
        [pairs, updatePairs],
    );

    const addRow = useCallback(() => {
        updatePairs([...pairs, { key: "", value: "" }]);
    }, [pairs, updatePairs]);

    const removeRow = useCallback(
        (index: number) => {
            const newPairs = pairs.filter((_, i) => i !== index);
            // Ensure we maintain minimum rows
            updatePairs(newPairs);
        },
        [pairs, updatePairs],
    );

    return (
        <div className={cn("space-y-2", className)}>
            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[40%]">Key</TableHead>
                            <TableHead className="w-[40%]">Value</TableHead>
                            <TableHead className="w-[20%] text-center">Delete</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {pairs.map((pair, index) => (
                            <TableRow key={index}>
                                <TableCell className="p-2">
                                    <Input
                                        value={pair.key}
                                        onChange={(e) => handleKeyChange(index, e.target.value)}
                                        placeholder={keyPlaceholder}
                                        disabled={disabled}
                                        className="border-0 shadow-none focus-visible:ring-0 bg-transparent"
                                    />
                                </TableCell>
                                <TableCell className="p-2">
                                    <Input
                                        value={pair.value}
                                        onChange={(e) => handleValueChange(index, e.target.value)}
                                        placeholder={valuePlaceholder}
                                        disabled={disabled}
                                        className="border-0 shadow-none focus-visible:ring-0 bg-transparent"
                                    />
                                </TableCell>
                                <TableCell className="p-2 text-center">
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => removeRow(index)}
                                        disabled={disabled}
                                        className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                                    >
                                        <X className="h-4 w-4" />
                                        <span className="sr-only">Remove row</span>
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>

            {
                <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addRow}
                    disabled={disabled}
                    className="w-full"
                >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Row
                </Button>
            }
        </div>
    );
}
// FIXME: hideous
export function keyValuePairsFromObject(obj: Record<string, any>): KeyValuePair[] {
    if (obj == null || Object.keys(obj).length === 0) {
        return [];
    }
    return Object.entries(obj).map(([key, value]) => ({
        key,
        value: typeof value === "string" ? value : JSON.stringify(value),
    }));
}

/**
 * Utility function to convert key-value pairs to a map object
 */
export function keyValuePairsToMap(pairs: KeyValuePair[]): Map<string, string> {
    if (pairs == null || pairs.length === 0) {
        return new Map<string, string>();
    }

    const result = new Map<string, string>();
    pairs.forEach((pair) => {
        if (pair.key && pair.key.trim() !== "") {
            result.set(pair.key.trim(), pair.value || "");
        }
    });
    return result;
}

/**
 * Utility function to convert a JSON object to key-value pairs
 */
export function jsonToKeyValuePairs(json: Record<string, any>): KeyValuePair[] {
    return Object.entries(json).map(([key, value]) => ({
        key,
        value: typeof value === "string" ? value : JSON.stringify(value),
    }));
}
