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

type NameTypeTuple = [name: string, type: "FIXED" | "ENVIRONMENT" | "RUNTIME"];

export interface ExpandableListProps {
    /** Array of name-type tuples */
    value?: NameTypeTuple[];
    /** Called when the list items change */
    onChange?: (items: NameTypeTuple[]) => void;
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
    const [items, setItems] = useState<NameTypeTuple[]>(() => {
        if (value == null || value.length === 0) {
            return [];
        }
        return value.map((item) => item || (["", "FIXED"] as NameTypeTuple));
    });

    const updateItems = useCallback(
        (newItems: NameTypeTuple[]) => {
            setItems(newItems);
            onChange?.(newItems.filter(([itemName, itemType]) => (itemName || "").trim() !== ""));
        },
        [onChange],
    );

    const handleItemChange = useCallback(
        (index: number, newValue: NameTypeTuple) => {
            const newItems = [...items];
            newItems[index] = newValue;
            updateItems(newItems);
        },
        [items, updateItems],
    );

    const addRow = useCallback(() => {
        updateItems([...items, ["", "FIXED"] as NameTypeTuple]);
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
                                        value={item[0]}
                                        onChange={(e) =>
                                            handleItemChange(index, [e.target.value, item[1]])
                                        }
                                        placeholder={placeholder}
                                        disabled={disabled}
                                        className="border-0 shadow-none focus-visible:ring-0 bg-transparent"
                                    />
                                </TableCell>
                                <TableCell className="p-2">
                                    <SelectableType
                                        disabled={disabled}
                                        value={item[1]}
                                        onChange={(newType) =>
                                            handleItemChange(index, [item[0], newType])
                                        }
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
        </div>
    );
}

function SelectableType({
    disabled = false,
    value,
    onChange,
}: {
    disabled?: boolean;
    value: "FIXED" | "ENVIRONMENT" | "RUNTIME";
    onChange: (value: "FIXED" | "ENVIRONMENT" | "RUNTIME") => void;
}) {
    return (
        <Select value={value} onValueChange={onChange} disabled={disabled}>
            <SelectTrigger>
                <SelectValue placeholder="Select type" />
            </SelectTrigger>
            <SelectContent>
                <SelectItem value="FIXED">Fixed</SelectItem>
                <SelectItem value="ENVIRONMENT">Environment</SelectItem>
                <SelectItem value="RUNTIME">Runtime</SelectItem>
            </SelectContent>
        </Select>
    );
}

export function listToJsonString(items: NameTypeTuple[]): string {
    if (items == null || items.length === 0) {
        return "[]";
    }
    if (!Array.isArray(items)) {
        throw new Error("Input must be an array of tuples");
    }

    const formattedVariables = items
        .filter(([itemName]) => itemName.trim() !== "")
        .map(([itemName, itemType]) => {
            if (itemType === "ENVIRONMENT") {
                return { env: itemName };
            }
            if (itemType === "RUNTIME") {
                return { param: itemName };
            }
            // Default case for "FIXED"
            return { value: itemName }; // Default case
        });
    return JSON.stringify(formattedVariables);
}

export function jsonStringToExpandableList(jsonString: string): NameTypeTuple[] {
    const parsed = JSON.parse(jsonString).catch(() => {
        return [];
    });
    if (!Array.isArray(parsed)) {
        return [];
    }

    return parsed.map((item) => {
        if (item.env) {
            return [item.env, "ENVIRONMENT"] as NameTypeTuple;
        }
        if (item.param) {
            return [item.param, "RUNTIME"] as NameTypeTuple;
        }
        if (item.value) {
            return [item.value, "FIXED"] as NameTypeTuple;
        }
        return ["", "FIXED"] as NameTypeTuple; // Default case for empty or unknown items
    });
}
