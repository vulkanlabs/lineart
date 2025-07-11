"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, useFieldArray } from "react-hook-form";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { TrashIcon } from "lucide-react";
import { toast } from "sonner";
import { ConfigurationVariablesBase } from "@vulkanlabs/client-open";

const environmentVariableSchema = z.object({
    name: z
        .string()
        .regex(/^[a-zA-Z0-9_]+$/, {
            message: "Variable name can only contain alphanumeric characters and underscores.",
        })
        .min(1, "Variable name cannot be empty."),
    value: z.string(),
    isNew: z.boolean().optional(),
    isNameEditable: z.boolean().optional(),
});

const configVariablesSchema = z.object({
    variables: z.array(environmentVariableSchema),
});

export interface EnvironmentVariablesEditorProps {
    variables: ConfigurationVariablesBase[];
    requiredVariableNames?: string[];
    onSave: (variables: ConfigurationVariablesBase[]) => Promise<void>;
    isLoading?: boolean;
    readOnly?: boolean;
    showAddButton?: boolean;
    showRemoveButton?: boolean;
    showSaveCancelButtons?: boolean;
    className?: string;
}

export function EnvironmentVariablesEditor({
    variables: initialVariables,
    requiredVariableNames = [],
    onSave,
    isLoading = false,
    readOnly = false,
    showAddButton = true,
    showRemoveButton = true,
    showSaveCancelButtons = true,
    className = "",
}: EnvironmentVariablesEditorProps) {
    const [saving, setSaving] = useState(false);
    const initialValues =
        initialVariables.map((v) => ({
            name: v.name,
            value: String(v.value || ""),
        })) || [];

    const form = useForm<z.infer<typeof configVariablesSchema>>({
        resolver: zodResolver(configVariablesSchema),
        values: {
            variables: initialValues,
        },
    });

    const { fields, append, remove } = useFieldArray({
        control: form.control,
        name: "variables",
    });
    const isModified = form.formState.isDirty;
    const onSubmit = async (data: z.infer<typeof configVariablesSchema>) => {
        setSaving(true);
        try {
            const variables = data.variables.map(
                ({ isNew, isNameEditable, ...rest }) => rest as ConfigurationVariablesBase,
            );
            await onSave(variables);
            form.reset({
                variables: data.variables.map((v) => ({
                    ...v,
                    isNew: false,
                    isNameEditable: !!v.isNew,
                })),
            });
            toast("Environment variables saved", {
                description: "Your environment variables have been updated.",
            });
        } catch (error) {
            console.error(error);
            toast("Error saving environment variables", {
                description:
                    (error as Error)?.message ||
                    "There was a problem updating your environment variables.",
            });
        } finally {
            setSaving(false);
        }
    };
    const onCancel = () => {
        form.reset({ variables: initialValues });
    };
    const currentVariableMap = new Map(form.getValues().variables.map((v) => [v.name, v.value]));
    const missingOrEmptyRequiredVariables = requiredVariableNames.filter(
        (name) => !currentVariableMap.has(name) || currentVariableMap.get(name) === "",
    );
    return (
        <div className={`space-y-4 ${className}`}>
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <div className="flex flex-row justify-between items-center">
                        <div className="text-sm text-muted-foreground">
                            Define environment variables.
                            {missingOrEmptyRequiredVariables.length > 0 && (
                                <p className="text-orange-500 text-xs mt-1">
                                    {
                                        "Warning: The following required variables are missing or empty: "
                                    }
                                    {missingOrEmptyRequiredVariables.join(", ")}
                                </p>
                            )}
                        </div>
                        {showSaveCancelButtons && (
                            <div className="flex space-x-2">
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={onCancel}
                                    disabled={isLoading || saving || !isModified || readOnly}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    type="submit"
                                    disabled={
                                        isLoading ||
                                        saving ||
                                        !isModified ||
                                        !form.formState.isValid ||
                                        readOnly
                                    }
                                    variant={isModified ? "default" : "outline"}
                                >
                                    {saving ? "Saving..." : "Save Variables"}
                                </Button>
                            </div>
                        )}
                    </div>
                    <div className="space-y-2">
                        {fields.map((field, index) => (
                            <div
                                key={field.id}
                                className="flex items-center space-x-2 p-2 border rounded-md"
                            >
                                <FormField
                                    control={form.control}
                                    name={`variables.${index}.name`}
                                    render={({ field: nameField }) => (
                                        <FormItem className="flex-1">
                                            <FormControl>
                                                <Input
                                                    {...nameField}
                                                    placeholder="Variable Name (e.g., API_KEY)"
                                                    className="font-mono"
                                                    readOnly={
                                                        readOnly ||
                                                        (!form.getValues().variables[index]
                                                            ?.isNameEditable &&
                                                            !form.getValues().variables[index]
                                                                ?.isNew)
                                                    }
                                                />
                                            </FormControl>
                                            <FormMessage className="text-red-500" />
                                        </FormItem>
                                    )}
                                />
                                <FormField
                                    control={form.control}
                                    name={`variables.${index}.value`}
                                    render={({ field: valueField }) => (
                                        <FormItem className="flex-1">
                                            <FormControl>
                                                <Input
                                                    {...valueField}
                                                    placeholder="Variable Value"
                                                    className="font-mono"
                                                    readOnly={readOnly}
                                                />
                                            </FormControl>
                                            <FormMessage className="text-red-500" />
                                        </FormItem>
                                    )}
                                />
                                {showRemoveButton && !readOnly && (
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => remove(index)}
                                        disabled={isLoading || saving}
                                    >
                                        <TrashIcon className="h-4 w-4" />
                                    </Button>
                                )}
                            </div>
                        ))}
                    </div>
                    {showAddButton && !readOnly && (
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() =>
                                append({ name: "", value: "", isNew: true, isNameEditable: true })
                            }
                            disabled={isLoading || saving}
                        >
                            Add Variable
                        </Button>
                    )}
                </form>
            </Form>
        </div>
    );
}
