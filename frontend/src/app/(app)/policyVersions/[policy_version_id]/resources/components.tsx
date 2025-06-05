"use client";
import { LinkIcon, TrashIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, useFieldArray } from "react-hook-form";
import * as z from "zod";

import { DataTable } from "@/components/data-table";
import { ShortenedID } from "@/components/shortened-id";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
import { ConfigurationVariables } from "@vulkan-server/ConfigurationVariables";
import { ConfigurationVariablesBase } from "@vulkan-server/ConfigurationVariablesBase";
import { DataSource } from "@vulkan-server/DataSource";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { updatePolicyVersion, setPolicyVersionVariables } from "@/lib/api";
import { toast } from "sonner";
import { setPolicyVersionVariablesAction } from "./actions";

function parseNullableDate(rawDate: string | null): string {
    if (rawDate === null) {
        return "N/A";
    }

    return parseDate(rawDate);
}

const ConfigVariablesTableColumns: ColumnDef<ConfigurationVariables>[] = [
    {
        accessorKey: "name",
        header: "Name",
    },
    {
        accessorKey: "value",
        header: "Value",
    },
    {
        accessorKey: "created_at",
        header: "Created At",
        cell: ({ row }) => parseNullableDate(row.getValue("created_at")),
    },
    {
        accessorKey: "last_updated_at",
        header: "Last Updated At",
        cell: ({ row }) => parseNullableDate(row.getValue("last_updated_at")),
    },
];

export function ConfigVariablesTable({
    policyVersion,
    variables: initialVariables,
}: {
    policyVersion: PolicyVersion;
    variables: ConfigurationVariables[];
}) {
    const [isLoading, setIsLoading] = useState(false);
    const form = useForm<z.infer<typeof configVariablesSchema>>({
        resolver: zodResolver(configVariablesSchema),
        defaultValues: {
            variables:
                initialVariables.map((v) => ({
                    ...v,
                    value: String(v.value || ""), // Ensure value is a string
                    isNew: false,
                    isNameEditable: false,
                })) || [],
        },
    });

    const { fields, append, remove } = useFieldArray({
        control: form.control,
        name: "variables",
    });

    const isModified = form.formState.isDirty;

    const onSubmit = async (data: z.infer<typeof configVariablesSchema>) => {
        setIsLoading(true);
        const variablesToSave = data.variables.map(
            ({ isNew, isNameEditable, ...rest }) => rest as ConfigurationVariablesBase,
        );
        try {
            setPolicyVersionVariablesAction(policyVersion.policy_version_id, variablesToSave);
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
                description: "There was a problem updating your environment variables.",
            });
        } finally {
            setIsLoading(false);
        }
    };

    const onCancel = () => {
        form.reset({
            variables:
                initialVariables.map((v) => ({
                    ...v,
                    value: String(v.value || ""), // Ensure value is a string
                    isNew: false,
                    isNameEditable: false,
                })) || [],
        });
    };

    // Use policyVersion.variables which contains the names of required variables
    const requiredVariableNames = policyVersion.variables || [];
    const currentVariableMap = new Map(form.getValues().variables.map((v) => [v.name, v.value]));
    const missingOrEmptyRequiredVariables = requiredVariableNames.filter(
        (name) => !currentVariableMap.has(name) || currentVariableMap.get(name) === "",
    );

    return (
        <div className="space-y-4">
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <div className="flex flex-row justify-between items-center">
                        <div className="text-sm text-muted-foreground">
                            Define environment variables for this policy version.
                            {missingOrEmptyRequiredVariables.length > 0 && (
                                <p className="text-orange-500 text-xs mt-1">
                                    {"Warning: The policy spec suggests these variables, " +
                                        "but they are missing or empty: "}
                                    {missingOrEmptyRequiredVariables.join(", ")}
                                </p>
                            )}
                        </div>
                        <div className="flex space-x-2">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={onCancel}
                                disabled={isLoading || !isModified}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                disabled={isLoading || !isModified || !form.formState.isValid}
                                variant={isModified ? "default" : "outline"}
                            >
                                {isLoading ? "Saving..." : "Save Variables"}
                            </Button>
                        </div>
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
                                                        !form.getValues().variables[index]
                                                            ?.isNameEditable &&
                                                        !form.getValues().variables[index]?.isNew
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
                                                />
                                            </FormControl>
                                            <FormMessage className="text-red-500" />
                                        </FormItem>
                                    )}
                                />
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => remove(index)}
                                    disabled={isLoading}
                                >
                                    <TrashIcon className="h-4 w-4" />
                                </Button>
                            </div>
                        ))}
                    </div>

                    <Button
                        type="button"
                        variant="outline"
                        onClick={() =>
                            append({ name: "", value: "", isNew: true, isNameEditable: true })
                        }
                        disabled={isLoading}
                    >
                        Add Variable
                    </Button>
                </form>
            </Form>
        </div>
    );
}

const DataSourceTableColumns: ColumnDef<DataSource>[] = [
    {
        accessorKey: "link",
        header: "",
        cell: ({ row }) => (
            <Link href={`/integrations/dataSources/${row.getValue("data_source_id")}`}>
                <LinkIcon />
            </Link>
        ),
    },
    {
        accessorKey: "name",
        header: "Data Source Name",
    },
    {
        accessorKey: "data_source_id",
        header: "Data Source ID",
        cell: ({ row }) => <ShortenedID id={row.getValue("data_source_id")} />,
    },
    {
        accessorKey: "created_at",
        header: "Created At",
        cell: ({ row }) => parseDate(row.getValue("created_at")),
    },
];

export function DataSourcesTable({ sources }) {
    return <DataTable columns={DataSourceTableColumns} data={sources} />;
}

export function RequirementsEditor({ policyVersion }: { policyVersion: PolicyVersion }) {
    const [isLoading, setIsLoading] = useState(false);

    const initialRequirements = policyVersion.requirements.toString().replaceAll(",", "\n") || "";
    const form = useForm<z.infer<typeof requirementsSchema>>({
        resolver: zodResolver(requirementsSchema),
        defaultValues: {
            requirements: initialRequirements,
        },
    });

    const isModified = form.formState.isDirty;

    const onSubmit = async (data: z.infer<typeof requirementsSchema>) => {
        setIsLoading(true);
        const formattedRequirements = data.requirements.split("\n").map((line) => line.trim());
        try {
            await updatePolicyVersion(policyVersion.policy_version_id, {
                requirements: formattedRequirements,
                alias: policyVersion.alias,
                input_schema: policyVersion.input_schema,
                spec: policyVersion.spec,
                ui_metadata: policyVersion.ui_metadata,
            });
            form.reset({ requirements: data.requirements });
            toast("Requirements saved", {
                description: "Your Python requirements have been updated.",
            });
        } catch (error) {
            console.error(error);
            toast("Error saving requirements", {
                description: "There was a problem updating your requirements.",
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="space-y-4">
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <div className="flex flex-row justify-between">
                        <div className="text-sm text-muted-foreground">
                            Define your custom Python package requirements, one per line (e.g.,
                            pandas==1.5.3)
                        </div>
                        <Button
                            type="submit"
                            disabled={isLoading || !isModified}
                            variant={isModified ? "default" : "outline"}
                        >
                            {isLoading ? "Saving..." : "Save Requirements"}
                        </Button>
                    </div>

                    <FormField
                        control={form.control}
                        name="requirements"
                        render={({ field }) => (
                            <FormItem>
                                <FormControl>
                                    <Textarea
                                        {...field}
                                        className="font-mono h-64"
                                        placeholder={exampleRequirements}
                                    />
                                </FormControl>
                                <FormMessage className="text-red-500" />
                            </FormItem>
                        )}
                    />
                </form>
            </Form>
        </div>
    );
}

const requirementsSchema = z.object({
    requirements: z.string().refine(
        (value) => {
            const lines = value.split("\n");
            for (const line of lines) {
                const trimmedLine = line.trim();
                if (trimmedLine === "" || trimmedLine.startsWith("#")) continue;
                if (/[^a-zA-Z\d\-_.=<>!~\^]/.test(trimmedLine)) {
                    return false;
                }
            }
            return true;
        },
        {
            message:
                "Requirements contain invalid characters. " +
                "Use only letters, numbers, and common symbols like =, <, >, -, _, ., ^, ~, !",
        },
    ),
});

const exampleRequirements = `# Example requirements
numpy==1.24.3
pandas>=1.5.0
scikit-learn<2
`;

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
