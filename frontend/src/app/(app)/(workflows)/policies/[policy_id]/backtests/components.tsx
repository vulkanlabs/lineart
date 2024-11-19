"use client";
import React, { useState } from "react";
import { useUser } from "@stackframe/stack";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
    Form,
    FormField,
    FormControl,
    FormDescription,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export async function FileUploaderPage({ uploadFn }) {
    const [error, setError] = useState<Error>(null);
    const [fileId, setFileId] = useState<string | null>(null);

    const user = useUser();
    const authJson = await user.getAuthJson();
    const headers = {
        "x-stack-access-token": authJson.accessToken,
        "x-stack-refresh-token": authJson.refreshToken,
    };

    return (
        <div className="flex flex-col p-8 gap-8">
            <h1 className="text-2xl font-bold tracking-tight">Uploader</h1>
            <div>
                <FileUploader
                    setFileId={setFileId}
                    setError={setError}
                    uploadFn={uploadFn}
                    headers={headers}
                />
            </div>
            {fileId && <FileUploadedCard fileId={fileId} />}
            {error && <UploadErrorCard error={error} />}
        </div>
    );
}

const formSchema = z.object({
    file: typeof window === "undefined" ? z.any() : z.instanceof(FileList),
    file_format: z.string(),
    schema: z.string().refine(ensureJSON, { message: "Not a valid JSON object" }),
});

function FileUploader({ setFileId, setError, uploadFn, headers }) {
    const [submitting, setSubmitting] = useState(false);

    const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const uploadUrl = `${serverUrl}/backtests/files`;

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
    });

    async function onSubmit(values: z.infer<typeof formSchema>) {
        const body = new FormData();
        body.append("file", values.file[0]);
        body.append("file_format", values.file_format);
        body.append("schema", values.schema);
        
        setSubmitting(true);
        setError(null);
        setFileId(null);

        uploadFn({ uploadUrl, body, headers })
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
                    <form onSubmit={form.handleSubmit(onSubmit)}>
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

function FileUploadedCard({ fileId }) {
    return (
        <Card className="flex flex-col w-fit border-green-600 border-2">
            <CardHeader>
                <CardTitle>Uploaded file successfully</CardTitle>
                <CardDescription>
                    File uploaded with id <strong>{fileId}</strong>.
                </CardDescription>
            </CardHeader>
        </Card>
    );
}

function UploadErrorCard({ error }) {
    console.log(error);
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
