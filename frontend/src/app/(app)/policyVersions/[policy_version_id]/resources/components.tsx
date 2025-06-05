"use client";
import { LinkIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";

import { DataTable } from "@/components/data-table";
import { ShortenedID } from "@/components/shortened-id";
import { parseDate } from "@/lib/utils";
import { ColumnDef } from "@tanstack/react-table";
import { DataSource } from "@vulkan-server/DataSource";
import { PolicyVersion } from "@vulkan-server/PolicyVersion";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form";
import { updatePolicyVersion } from "@/lib/api";
import { toast } from "sonner";
import {
    EnvironmentVariablesEditor,
    EnvironmentVariablesEditorProps,
} from "@/components/environment-variables-editor";
import { setPolicyVersionVariablesAction } from "./actions";

interface EnvironmentVariablesProps {
    policyVersion: PolicyVersion;
    variables: EnvironmentVariablesEditorProps["variables"];
}

export function EnvironmentVariables({ policyVersion, variables }: EnvironmentVariablesProps) {
    return (
        <EnvironmentVariablesEditor
            variables={variables}
            requiredVariableNames={policyVersion?.variables || []}
            onSave={async (updatedVariables) => {
                await setPolicyVersionVariablesAction(
                    policyVersion.policy_version_id,
                    updatedVariables,
                );
            }}
        />
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
