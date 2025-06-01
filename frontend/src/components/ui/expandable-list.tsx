"use client";

import React, { useState, useCallback } from "react";
import { Plus, X } from "lucide-react";
import { Button } from "./button";
import { Input } from "./input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./table";
import { cn } from "@/lib/utils";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

export interface ExpandableListProps {
    /** Array of string values */
    value?: string[];
    /** Called when the list items change */
    onChange?: (items: string[]) => void;
    /** Placeholder text for the input */
    placeholder?: string;
    /** Whether the table is disabled */
    disabled?: boolean;
    /** Custom className for the container */
    className?: string;
    /** Minimum number of rows to show */
    minRows?: number;
    /** Maximum number of rows allowed */
    maxRows?: number;
    /** Label for the column header */
    label?: string;
}

export function ExpandableList({
    value = [],
    onChange,
    placeholder = "Enter value",
    disabled = false,
    className,
    label = "Value",
}: ExpandableListProps) {
    const [items, setItems] = useState<string[]>(() => {
        if (value == null || value.length === 0) {
            return [];
        }
        return value.map((item) => item || "");
    });

    const updateItems = useCallback(
        (newItems: string[]) => {
            setItems(newItems);
            onChange?.(newItems.filter((item) => (item || "").trim() !== ""));
        },
        [onChange],
    );

    const handleItemChange = useCallback(
        (index: number, newValue: string) => {
            const newItems = [...items];
            newItems[index] = newValue;
            updateItems(newItems);
        },
        [items, updateItems],
    );

    const addRow = useCallback(() => {
        updateItems([...items, ""]);
    }, [items, updateItems]);

    const removeRow = useCallback(
        (index: number) => {
            const newItems = items.filter((_, i) => i !== index);
            updateItems(newItems);
        },
        [items, updateItems],
    );

    return (
        <div className={cn("space-y-2", className)}>
            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[60%]">{label}</TableHead>
                            <TableHead className="w-[20%]">Type</TableHead>
                            <TableHead className="w-[20%] text-center">Delete</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {items.map((item, index) => (
                            <TableRow key={index}>
                                <TableCell className="p-2">
                                    <Input
                                        value={item}
                                        onChange={(e) => handleItemChange(index, e.target.value)}
                                        placeholder={placeholder}
                                        disabled={disabled}
                                        className="border-0 shadow-none focus-visible:ring-0 bg-transparent"
                                    />
                                </TableCell>
                                <TableCell className="p-2">
                                    <SelectableType disabled={disabled} />
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
                    Add Item
                </Button>
            }
        </div>
    );
}

function SelectableType({ disabled = false }: { disabled?: boolean }) {
    const [value, setValue] = useState<string>("FIXED");

    return (
        <Select value={value} onValueChange={setValue} disabled={disabled}>
            <SelectTrigger>
                <SelectValue placeholder="Select HTTP method" />
            </SelectTrigger>
            <SelectContent>
                <SelectItem value="FIXED">Fixed</SelectItem>
                <SelectItem value="ENVIRONMENT">Environment</SelectItem>
                <SelectItem value="RUNTIME">Runtime</SelectItem>
            </SelectContent>
        </Select>
    );
}

/**
 * Utility function to convert array of strings to JSON string
 */
export function listToJsonString(items: string[]): string {
    if (items == null || items.length === 0) {
        return "[]";
    }
    if (!Array.isArray(items)) {
        throw new Error("Input must be an array of strings");
    }

    console.log("passing items to JSON string:", items);
    return JSON.stringify(items.filter((item) => item.trim() !== ""));
}

/**
 * Utility function to convert JSON string to array of strings
 */
export function jsonStringToList(jsonString: string): string[] {
    try {
        const parsed = JSON.parse(jsonString);
        if (Array.isArray(parsed)) {
            return parsed.map((item) => (typeof item === "string" ? item : String(item)));
        }
        return [];
    } catch (error) {
        return [];
    }
}
