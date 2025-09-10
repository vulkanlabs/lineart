"use client";

import React, { useState, useEffect } from "react";
import { type NodeChange } from "@xyflow/react";
import { PlusIcon, Trash2 } from "lucide-react";
import { useShallow } from "zustand/react/shallow";
import { z } from "zod";

import {
    Button,
    Input,
    Label,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@vulkanlabs/base/ui";

import { InputWorkflowNode } from "./base";
import { useWorkflowStore } from "@/workflow/store";
import type { VulkanNodeProps, VulkanNode } from "@/workflow/types/workflow";
import type { InputNodeMetadata } from "@/workflow/types/nodes";

// Zod schema for field name validation
const fieldNameSchema = z
    .string()
    .regex(/^[a-z0-9_]+$/, "Field names must be lowercase alphanumeric or underscores")
    .min(1, "Field name cannot be empty");

const fieldTypes = ["str", "int", "float", "bool"];

/**
 * Input node component - specialized workflow node for data input
 */
export function InputNode({ id, data, selected, width }: VulkanNodeProps) {
    const [editingFields, setEditingFields] = useState<Record<string, string>>({});
    const [invalidFields, setInvalidFields] = useState<Record<string, string>>({});
    const { updateNodeData, onNodesChange } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            onNodesChange: state.onNodesChange,
        })),
    );

    // Use effect to update fieldOrder when schema changes
    const [fieldOrder, setFieldOrder] = useState(() =>
        Object.keys(data.metadata?.schema || {}).length > 0
            ? Object.keys(data.metadata.schema)
            : [],
    );

    // Add an effect to keep fieldOrder in sync with data.metadata.schema
    useEffect(() => {
        const schemaKeys = Object.keys(data.metadata?.schema || {});

        // Keep only valid keys that exist in the schema
        const validFieldOrder = fieldOrder.filter((field) => schemaKeys.includes(field));

        // Add any new keys that aren't yet in fieldOrder
        const newKeys = schemaKeys.filter((key) => !validFieldOrder.includes(key));

        if (newKeys.length > 0 || validFieldOrder.length !== fieldOrder.length) {
            setFieldOrder([...validFieldOrder, ...newKeys]);
        }
    }, [data.metadata?.schema, fieldOrder]);

    const handleAddField = () => {
        const schema = data.metadata?.schema || {};

        // Find the next available field number
        let fieldNumber = 1;
        while (schema[`field_${fieldNumber}`]) {
            fieldNumber++;
        }
        const newFieldName = `field_${fieldNumber}`;

        const updatedSchema = {
            ...schema,
            [newFieldName]: "str",
        };
        const metadata: InputNodeMetadata = { schema: updatedSchema };

        setFieldOrder([...fieldOrder, newFieldName]);
        updateNodeData(id, { ...data, metadata });
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

    const handleRemoveField = (fieldName: string) => {
        const updatedSchema = { ...(data.metadata?.schema || {}) } as Record<string, string>;
        delete updatedSchema[fieldName];

        // Clean up any editing state for this field
        const updatedEditingFields = { ...editingFields };
        delete updatedEditingFields[fieldName];
        setEditingFields(updatedEditingFields);

        // Clean up any validation state
        const updatedInvalidFields = { ...invalidFields };
        delete updatedInvalidFields[fieldName];
        setInvalidFields(updatedInvalidFields);

        // Update node data first, then update field order to ensure they stay in sync
        const metadata: InputNodeMetadata = { schema: updatedSchema };
        updateNodeData(id, {
            ...data,
            metadata,
        });

        // Update field order after updating node data
        setFieldOrder((prev) => prev.filter((name) => name !== fieldName));

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

    const startEditingField = (fieldName: string) => {
        // When starting to edit, always initialize with the current field name
        // This ensures we're always starting from a valid state
        setEditingFields({
            ...editingFields,
            [fieldName]: fieldName,
        });

        // Clear any existing validation errors for this field when starting editing
        if (invalidFields[fieldName]) {
            const updatedInvalidFields = { ...invalidFields };
            delete updatedInvalidFields[fieldName];
            setInvalidFields(updatedInvalidFields);
        }
    };

    const handleFieldNameChange = (oldName: string, newValue: string) => {
        // Update the editing state with the new value
        setEditingFields({
            ...editingFields,
            [oldName]: newValue,
        });

        // Perform validation on the new name
        const updatedInvalidFields = { ...invalidFields };
        const schema = (data.metadata?.schema || {}) as Record<string, string>;

        // Validate the new name
        const validationResult = fieldNameSchema.safeParse(newValue);

        if (!validationResult.success) {
            // Format validation failed
            updatedInvalidFields[oldName] = validationResult.error.issues[0].message;
        } else if (newValue !== oldName && Object.keys(schema).includes(newValue)) {
            // Check for duplicate - use Object.keys for a more reliable check
            updatedInvalidFields[oldName] = "Field name already exists";
        } else {
            // Clear error if now valid
            delete updatedInvalidFields[oldName];
        }

        setInvalidFields(updatedInvalidFields);
    };

    const commitFieldNameChange = (oldName: string) => {
        // If there's no editing state for this field, do nothing
        if (editingFields[oldName] === undefined) {
            return;
        }

        const newName = editingFields[oldName];

        // If field name is invalid, keep the user's input but don't update the schema
        if (invalidFields[oldName]) {
            return;
        }

        // Don't proceed if there's no change
        if (oldName === newName) {
            // Just clear the editing state
            const updatedEditingFields = { ...editingFields };
            delete updatedEditingFields[oldName];
            setEditingFields(updatedEditingFields);
            return;
        }

        // Create a new schema while preserving field order
        const updatedSchema = {} as Record<string, string>;
        const schema = (data.metadata?.schema || {}) as Record<string, string>;
        const fieldType = schema[oldName];

        // Update field order array
        const newFieldOrder = fieldOrder.map((name) => (name === oldName ? newName : name));

        // Rebuild schema in the correct order
        newFieldOrder.forEach((fieldName) => {
            updatedSchema[fieldName] = fieldName === newName ? fieldType : schema[fieldName];
        });

        // Clean up editing state
        const updatedEditingFields = { ...editingFields };
        delete updatedEditingFields[oldName];
        setEditingFields(updatedEditingFields);

        // Clean up any validation state
        const updatedInvalidFields = { ...invalidFields };
        delete updatedInvalidFields[oldName];
        setInvalidFields(updatedInvalidFields);

        // Update the field order and node data
        setFieldOrder(newFieldOrder);
        updateNodeData(id, {
            ...data,
            metadata: { schema: updatedSchema },
        });
    };

    const handleFieldTypeChange = (fieldName: string, newType: string) => {
        const schema = data.metadata?.schema || {};
        updateNodeData(id, {
            ...data,
            metadata: {
                schema: {
                    ...schema,
                    [fieldName]: newType,
                },
            },
        });
    };

    return (
        <InputWorkflowNode id={id} selected={selected} data={data} width={width}>
            <div className="flex flex-col p-4 w-full h-fit space-y-4">
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <Label className="text-sm font-medium">Schema Fields</Label>
                    </div>
                    {fieldOrder.length > 0 && (
                        <div className="grid grid-cols-[2fr_80px_auto] gap-3 items-center pb-2 border-b border-gray-200">
                            <Label className="text-xs font-medium text-gray-600">Name</Label>
                            <Label className="text-xs font-medium text-gray-600">Type</Label>
                            <div></div>
                        </div>
                    )}
                    {fieldOrder.map((fieldName) => {
                        const schema = (data.metadata?.schema || {}) as Record<string, string>;
                        const fieldType = schema[fieldName];
                        return (
                            <div
                                key={fieldName}
                                className="grid grid-cols-[2fr_80px_auto] gap-3 items-center"
                            >
                                <div className="space-y-1">
                                    <div
                                        className="nodrag"
                                        onMouseDown={(e) => e.stopPropagation()}
                                    >
                                        <Input
                                            type="text"
                                            className={`h-8 ${
                                                invalidFields[fieldName]
                                                    ? "border-red-400 focus:border-red-500"
                                                    : ""
                                            }`}
                                            value={
                                                editingFields[fieldName] !== undefined
                                                    ? editingFields[fieldName]
                                                    : fieldName
                                            }
                                            onChange={(e) =>
                                                handleFieldNameChange(fieldName, e.target.value)
                                            }
                                            onFocus={() => startEditingField(fieldName)}
                                            onBlur={() => commitFieldNameChange(fieldName)}
                                            placeholder="field_name"
                                        />
                                    </div>
                                    {invalidFields[fieldName] && (
                                        <div className="text-red-500 text-[10px]">
                                            {invalidFields[fieldName]}
                                        </div>
                                    )}
                                </div>
                                <Select
                                    value={fieldType}
                                    onValueChange={(value) =>
                                        handleFieldTypeChange(fieldName, value)
                                    }
                                >
                                    <SelectTrigger
                                        className="h-8"
                                        onMouseDown={(e) => e.stopPropagation()}
                                    >
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {fieldTypes.map((type) => (
                                            <SelectItem key={type} value={type}>
                                                {type}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleRemoveField(fieldName)}
                                    className="h-6 w-6 p-0"
                                >
                                    <Trash2 className="h-3 w-3" />
                                </Button>
                            </div>
                        );
                    })}
                    {fieldOrder.length === 0 && (
                        <div
                            className="flex flex-col items-center justify-center text-gray-500 py-8 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 hover:border-gray-400 transition-all duration-200"
                            onClick={handleAddField}
                        >
                            <PlusIcon className="w-8 h-8 mb-3 text-gray-400" />
                            <span className="text-sm font-medium text-gray-600 mb-1">
                                Click to add a field
                            </span>
                            <span className="text-xs text-gray-400">Define your input schema</span>
                        </div>
                    )}
                </div>

                {fieldOrder.length > 0 && (
                    <div className="mt-2">
                        <Button
                            variant="outline"
                            className="w-full p-2 text-blue-600 border-blue-300 hover:bg-blue-50 hover:border-blue-400 transition-colors"
                            onClick={handleAddField}
                        >
                            <PlusIcon className="w-4 h-4 mr-2" />
                            Add field
                        </Button>
                    </div>
                )}
            </div>
        </InputWorkflowNode>
    );
}
