"use client";

// React and Next.js
import { useState } from "react";
import Link from "next/link";

// External libraries
import { useForm } from "react-hook-form";
import { LinkIcon } from "lucide-react";
import { zodResolver } from "@hookform/resolvers/zod";
import { ColumnDef } from "@tanstack/react-table";
import { toast } from "sonner";
import * as z from "zod";

// Vulkan packages
import {
    Button,
    Form,
    FormControl,
    FormField,
    FormItem,
    FormMessage,
    Textarea,
} from "@vulkanlabs/base/ui";
import {
    DataTable,
    EnvironmentVariablesEditor,
    ShortenedID,
    type EnvironmentVariablesEditorProps,
} from "@vulkanlabs/base";
import type {
    ConfigurationVariablesBase,
    DataSourceReference,
    PolicyVersion,
} from "@vulkanlabs/client-open";

// Local imports
import { updatePolicyVersion } from "@/lib/api";
import { parseDate } from "@vulkanlabs/base";


interface EnvironmentVariablesProps {
    policyVersion: PolicyVersion;
    variables: EnvironmentVariablesEditorProps["variables"];
}

export function EnvironmentVariables({ policyVersion, variables }: EnvironmentVariablesProps) {
    return (
        <EnvironmentVariablesEditor
            variables={variables}
            requiredVariableNames={policyVersion.workflow?.variables || []}
            onSave={async (updatedVariables: ConfigurationVariablesBase[]) => {
                await setPolicyVersionVariablesAction(
                    policyVersion.policy_version_id,
                    updatedVariables,
                );
            }}
        />
    );
}

const DataSourceTableColumns: ColumnDef<DataSourceReference>[] = [
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

export function DataSourcesTable({ sources }: { sources: DataSourceReference[] }) {
    return (
        <DataTable
            columns={DataSourceTableColumns}
            data={sources}
            emptyMessage="No data sources found"
            className=""
        />
    );
}

export function RequirementsEditor({ policyVersion }: { policyVersion: PolicyVersion }) {
    const [isLoading, setIsLoading] = useState(false);

    // Safely handle requirements conversion with proper null checking
    const initialRequirements = policyVersion.workflow?.requirements
        ? Array.isArray(policyVersion.workflow.requirements)
            ? policyVersion.workflow.requirements.join("\n")
            : policyVersion.workflow.requirements.toString().replace(/,/g, "\n")
        : "";
    const form = useForm<z.infer<typeof requirementsSchema>>({
        resolver: zodResolver(requirementsSchema),
        defaultValues: {
            requirements: initialRequirements,
        },
    });

    const isModified = form.formState.isDirty;

    const onSubmit = async (data: z.infer<typeof requirementsSchema>) => {
        setIsLoading(true);
        const formattedRequirements = (data.requirements || "")
            .split("\n")
            .map((line) => line.trim())
            .filter((line) => line.length > 0);
        try {
            await updatePolicyVersion(policyVersion.policy_version_id, {
                alias: policyVersion.alias || null,
                workflow: {
                    requirements: formattedRequirements,
                    spec: policyVersion.workflow?.spec || {},
                    ui_metadata: policyVersion.workflow?.ui_metadata || null,
                },
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
                        render={({ field }: { field: any }) => (
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
                if (trimmedLine === "" || trimmedLine.startsWith("#")) {
                    continue;
                }
                if (/[^a-zA-Z\d\-_=.<>!~\^]/.test(trimmedLine)) {
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
