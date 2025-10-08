"use client";

import { CheckCircle, XCircle, Clock, Database } from "lucide-react";
import { Badge, Label } from "../ui";
import { JSONViewer } from "./JSONViewer";

interface TestResponse {
    status_code: number;
    response_body: any;
    response_time_ms: number;
    cache_hit: boolean;
    headers: Record<string, string>;
    request_url: string;
    error_message?: string;
}

interface TestResponsePanelProps {
    response: TestResponse | null;
    isLoading?: boolean;
}

/**
 * Panel displaying test response data
 * Shows status, headers, response time, and response body
 */
export function TestResponsePanel({ response, isLoading }: TestResponsePanelProps) {
    if (isLoading)
        return (
            <div className="flex flex-col h-full">
                <h3 className="text-base font-semibold mb-4">Response</h3>
                <div className="flex items-center justify-center flex-1 border border-border rounded-md bg-muted/20">
                    <div className="text-muted-foreground">Testing...</div>
                </div>
            </div>
        );

    if (!response)
        return (
            <div className="flex flex-col h-full">
                <h3 className="text-base font-semibold mb-4">Response</h3>
                <div className="flex items-center justify-center flex-1 border border-border rounded-md bg-muted/20">
                    <div className="text-muted-foreground">
                        Configure and run a test to see the response
                    </div>
                </div>
            </div>
        );

    const isSuccess = response.status_code >= 200 && response.status_code < 300;
    const isError = response.status_code >= 400;

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold">Response</h3>
                <div className="flex items-center gap-2">
                    {isSuccess && (
                        <Badge variant="default" className="bg-green-500">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Success
                        </Badge>
                    )}
                    {isError && (
                        <Badge variant="destructive">
                            <XCircle className="h-3 w-3 mr-1" />
                            Error
                        </Badge>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <Label>Status Code</Label>
                    <div className="mt-1.5 text-lg font-semibold">{response.status_code}</div>
                </div>
                <div>
                    <Label className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Response Time
                    </Label>
                    <div className="mt-1.5 text-lg font-semibold">{response.response_time_ms}ms</div>
                </div>
            </div>

            {response.cache_hit && (
                <div className="flex items-center gap-2 text-sm text-blue-600 p-2 bg-blue-50 border border-blue-200 rounded-md dark:bg-blue-950 dark:border-blue-800">
                    <Database className="h-4 w-4" />
                    <span>Cache Hit</span>
                </div>
            )}

            {response.error_message && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                    <div className="text-sm font-medium text-destructive">Error Message</div>
                    <div className="text-sm mt-1">{response.error_message}</div>
                </div>
            )}

            <div>
                <Label>Request URL</Label>
                <div className="mt-1.5 text-sm font-mono bg-muted p-2 rounded-md break-all">
                    {response.request_url}
                </div>
            </div>

            <div>
                <Label>Response Headers</Label>
                <div className="mt-1.5">
                    <JSONViewer data={response.headers} className="max-h-32" />
                </div>
            </div>

            <div>
                <Label>Response Body</Label>
                <div className="mt-1.5">
                    <JSONViewer data={response.response_body} className="max-h-96" />
                </div>
            </div>
        </div>
    );
}
