"use client";
import Link from "next/link";
import React, { useState } from "react";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { ArrowLeft } from "lucide-react";
import { Button } from "@vulkan/base/ui";
import {
    Form,
    FormField,
    FormControl,
    FormDescription,
    FormItem,
    FormLabel,
    FormMessage,
} from "@vulkan/base/ui";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@vulkan/base/ui";
import { Input } from "@vulkan/base/ui";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@vulkan/base/ui";
import { Textarea } from "@vulkan/base/ui";

export function FileUploaderPage({
    uploadFn,
    policyVersionId,
}: {
    uploadFn: any;
    policyVersionId: string;
}) {
    const [error, setError] = useState<Error>(null);
    const [fileId, setFileId] = useState<string | null>(null);

    return (
        <div className="flex flex-col py-4 px-8 gap-8">
            <Link href={`/policyVersions/${policyVersionId}/backtests`}>
                <button className="flex flex-row gap-2 bg-white text-black hover:text-gray-700 text-lg font-bold">
                    <ArrowLeft />
                    Back
                </button>
            </Link>
            <div>
                <FileUploader
                    policyVersionId={policyVersionId}
                    setFileId={setFileId}
                    setError={setError}
                    uploadFn={uploadFn}
                />
            </div>
            {fileId && <FileUploadedCard fileId={fileId} policyVersionId={policyVersionId} />}
            {error && <UploadErrorCard error={error} />}
        </div>
    );
}

const formSchema = z.object({
    file: typeof window === "undefined" ? z.any() : z.instanceof(FileList),
    file_format: z.string(),
    schema: z.string().refine(ensureJSON, { message: "Not a valid JSON object" }),
});

function FileUploader({ policyVersionId, setFileId, setError, uploadFn }) {
    const [submitting, setSubmitting] = useState(false);

    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const uploadUrl = `${serverUrl}/files`;

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
    });

    async function onSubmit(values: z.infer<typeof formSchema>) {
        const body = new FormData();
        body.append("file", values.file[0]);
        body.append("file_format", values.file_format);
        body.append("schema", values.schema);
        body.append("policy_version_id", policyVersionId);

        setSubmitting(true);
        setError(null);
        setFileId(null);

        uploadFn({ uploadUrl, body })
            .then((data) => {
                setError(null);
                setFileId(data.uploaded_file_id);
            })
            .catch((error) => {
                setError(error);
            })
            .finally(() => {
                setSubmitting(false);
            });
    }

    return <UploadFileFormCard form={form} onSubmit={onSubmit} submitting={submitting} />;
}

function UploadFileFormCard({ form, onSubmit, submitting }) {
    const fileRef = form.register("file");
    const placeholderText = JSON.stringify({ string_field: "str", integer_field: "int" }, null, 2);

    return (
        <Card>
            <CardHeader>
                <CardTitle>Upload Backtest File</CardTitle>
                <CardDescription>
                    Upload a file and its schema to use in a backtest pipeline.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <Form {...form}>
                    <form className="flex flex-col gap-4" onSubmit={form.handleSubmit(onSubmit)}>
                        <FormField
                            control={form.control}
                            name="file"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>File</FormLabel>
                                    <FormControl>
                                        <Input type="file" placeholder="shadcn" {...fileRef} />
                                    </FormControl>
                                    <FormDescription>File to be uploaded.</FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="file_format"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>File Format</FormLabel>
                                    <Select
                                        onValueChange={field.onChange}
                                        defaultValue={field.value}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select a file type" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            <SelectItem value="CSV">CSV</SelectItem>
                                            <SelectItem value="Parquet">Parquet</SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <FormDescription>Accepted file format.</FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="schema"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>File Schema</FormLabel>
                                    <FormControl>
                                        <Textarea
                                            className="min-h-40"
                                            placeholder={placeholderText}
                                            {...field}
                                        />
                                    </FormControl>
                                    <FormDescription>Schema for the file.</FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <div className="flex flex-row gap-4">
                            <Button type="submit" disabled={submitting}>
                                Upload
                            </Button>
                            {submitting && <p>Submitting...</p>}
                        </div>
                    </form>
                </Form>
            </CardContent>
        </Card>
    );
}

function ensureJSON(data: string) {
    try {
        JSON.parse(data);
        return true;
    } catch (e) {
        return false;
    }
}

function FileUploadedCard({ fileId, policyVersionId }) {
    return (
        <Card className="flex flex-col w-fit border-green-600 border-2">
            <CardHeader>
                <CardTitle>Uploaded file successfully</CardTitle>
                <CardDescription className="flex flex-col gap-4">
                    <div>
                        File uploaded with id <strong>{fileId}</strong>.
                    </div>
                    <Link href={`/policyVersions/${policyVersionId}/backtests`}>
                        <Button className="bg-green-600 hover:bg-green-500">Go to Table</Button>
                    </Link>
                </CardDescription>
            </CardHeader>
        </Card>
    );
}

function UploadErrorCard({ error }) {
    return (
        <Card className="flex flex-col w-fit border-red-600 border-2">
            <CardHeader>
                <CardTitle>Failed to upload file</CardTitle>
                <CardDescription>
                    Upload failed with error: <br />
                </CardDescription>
            </CardHeader>
            <CardContent>
                <pre className="text-wrap">{error.message}</pre>
            </CardContent>
        </Card>
    );
}
