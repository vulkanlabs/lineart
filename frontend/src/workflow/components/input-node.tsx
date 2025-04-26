import { useState, useEffect } from "react";
import { NodeProps, type NodeChange } from "@xyflow/react";
import { WorkflowNode } from "./base";
import { PlusIcon, TrashIcon } from "lucide-react";
import { useShallow } from "zustand/react/shallow";
import { z } from "zod";

import { useWorkflowStore } from "../store";
import { InputNodeMetadata, VulkanNode } from "../types";

// Zod schema for field name validation
const fieldNameSchema = z
    .string()
    .regex(/^[a-z0-9_]+$/, "Field names must be lowercase alphanumeric or underscores")
    .min(1, "Field name cannot be empty");

const fieldTypes = ["str", "int", "float", "bool"];

export function InputNode({ id, data, selected, width }: NodeProps<VulkanNode>) {
    const [editingFields, setEditingFields] = useState({});
    const [invalidFields, setInvalidFields] = useState({});
    const { updateNodeData, onNodesChange } = useWorkflowStore(
        useShallow((state) => ({
            updateNodeData: state.updateNodeData,
            onNodesChange: state.onNodesChange,
        })),
    );

    // Use effect to update fieldOrder when schema changes
    const [fieldOrder, setFieldOrder] = useState(() =>
        Object.keys(data.metadata.schema).length > 0 ? Object.keys(data.metadata.schema) : [],
    );

    // Add an effect to keep fieldOrder in sync with data.metadata.schema
    useEffect(() => {
        const schemaKeys = Object.keys(data.metadata.schema);

        // Keep only valid keys that exist in the schema
        const validFieldOrder = fieldOrder.filter((field) => schemaKeys.includes(field));

        // Add any new keys that aren't yet in fieldOrder
        const newKeys = schemaKeys.filter((key) => !validFieldOrder.includes(key));

        if (newKeys.length > 0 || validFieldOrder.length !== fieldOrder.length) {
            setFieldOrder([...validFieldOrder, ...newKeys]);
        }
    }, [data.metadata.schema, fieldOrder]);

    const handleAddField = () => {
        const newFieldName = `field_${Object.keys(data.metadata.schema).length + 1}`;
        const updatedSchema = {
            ...data.metadata.schema,
            [newFieldName]: "str",
        };
        const metadata: InputNodeMetadata = { schema: updatedSchema };

        setFieldOrder([...fieldOrder, newFieldName]);
        updateNodeData(id, { ...data, metadata });
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
    };

    const handleRemoveField = (fieldName: string) => {
        const updatedSchema = { ...data.metadata.schema };
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

        // Validate the new name
        const validationResult = fieldNameSchema.safeParse(newValue);

        if (!validationResult.success) {
            // Format validation failed
            updatedInvalidFields[oldName] = validationResult.error.issues[0].message;
        } else if (newValue !== oldName && Object.keys(data.metadata.schema).includes(newValue)) {
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
        const updatedSchema = {};
        const fieldType = data.metadata.schema[oldName];

        // Update field order array
        const newFieldOrder = fieldOrder.map((name) => (name === oldName ? newName : name));

        // Rebuild schema in the correct order
        newFieldOrder.forEach((fieldName) => {
            updatedSchema[fieldName] =
                fieldName === newName ? fieldType : data.metadata.schema[fieldName];
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
        updateNodeData(id, {
            ...data,
            metadata: {
                schema: {
                    ...data.metadata.schema,
                    [fieldName]: newType,
                },
            },
        });
    };

    return (
        <WorkflowNode
            id={id}
            selected={selected}
            data={data}
            width={width}
            isInput
            disableNameEditing
            disableFooter
        >
            <div className="flex flex-col p-2 w-full h-fit">
                <h3 className="text-sm font-semibold mb-2">Input Schema</h3>

                <div className="max-h-[300px] overflow-y-auto">
                    <table className="w-full text-xs">
                        <thead>
                            <tr className="border-b border-gray-200">
                                <th className="py-1 px-2 text-left">Field</th>
                                <th className="py-1 px-2 text-left">Type</th>
                                <th className="py-1 px-2 w-8"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {fieldOrder.map((fieldName) => {
                                const fieldType = data.metadata.schema[fieldName];
                                return (
                                    <tr key={fieldName} className="border-b border-gray-100">
                                        <td className="py-1 px-2">
                                            <div className="flex flex-col">
                                                <input
                                                    className={`w-full p-1 border rounded text-xs ${
                                                        invalidFields[fieldName]
                                                            ? "border-red-400"
                                                            : "border-gray-200"
                                                    }`}
                                                    value={
                                                        editingFields[fieldName] !== undefined
                                                            ? editingFields[fieldName]
                                                            : fieldName
                                                    }
                                                    onChange={(e) =>
                                                        handleFieldNameChange(
                                                            fieldName,
                                                            e.target.value,
                                                        )
                                                    }
                                                    onFocus={() => startEditingField(fieldName)}
                                                    onBlur={() => commitFieldNameChange(fieldName)}
                                                />
                                                {invalidFields[fieldName] && (
                                                    <div className="text-red-500 text-[10px] mt-1">
                                                        {invalidFields[fieldName]}
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="py-1 px-2">
                                            <select
                                                className="w-full p-1 border border-gray-200 rounded text-xs"
                                                value={fieldType}
                                                onChange={(e) =>
                                                    handleFieldTypeChange(fieldName, e.target.value)
                                                }
                                            >
                                                {fieldTypes.map((type) => (
                                                    <option key={type} value={type}>
                                                        {type}
                                                    </option>
                                                ))}
                                            </select>
                                        </td>
                                        <td className="py-1 px-2">
                                            <button
                                                className="p-1 hover:bg-gray-100 rounded"
                                                onClick={() => handleRemoveField(fieldName)}
                                            >
                                                <TrashIcon className="w-3 h-3 text-gray-500" />
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                            {fieldOrder.length === 0 && (
                                <tr>
                                    <td colSpan={3} className="py-2 text-center text-gray-500">
                                        No fields defined
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="mt-2 flex justify-between">
                    <button
                        className="px-2 py-1 text-xs bg-blue-50 text-blue-600
                         hover:bg-blue-100 rounded flex items-center"
                        onClick={handleAddField}
                    >
                        <PlusIcon className="w-3 h-3 mr-1" />
                        Add Field
                    </button>
                </div>
            </div>
        </WorkflowNode>
    );
}
