"use client";

import { CheckCircle, XCircle, Clock, Database } from "lucide-react";
import { Badge } from "../ui";
import { JSONViewer } from "./JSONViewer";

interface TestResponse {
    status_code: number;
    response_body: any;
    response_time_ms: number;
    cache_hit: boolean;
    request_url: string;
    request_headers?: Record<string, string>;
    response_headers?: Record<string, string>;
    error?: string;
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
                {isSuccess && (
                    <Badge variant="outline">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Success
                    </Badge>
                )}
                {isError && (
                    <Badge variant="outline" className="border-destructive text-destructive">
                        <XCircle className="h-3 w-3 mr-1" />
                        Error
                    </Badge>
                )}
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <p className="text-sm font-medium text-muted-foreground">Status Code</p>
                    <p className="text-lg font-semibold mt-1">{response.status_code}</p>
                </div>
                <div>
                    <p className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Response Time
                    </p>
                    <p className="text-lg font-semibold mt-1">
                        {Math.round(response.response_time_ms)}ms
                    </p>
                </div>
            </div>

            {response.cache_hit && (
                <div className="flex items-center gap-2 text-sm p-2 bg-muted/50 border rounded-md">
                    <Database className="h-4 w-4" />
                    <span>Cache Hit</span>
                </div>
            )}

            {(response.error || isError) && (
                <div className="p-3 bg-muted/50 border rounded-md">
                    <p className="text-sm font-medium mb-1">Error Details</p>
                    {response.error ? (
                        <p className="text-sm text-muted-foreground">{response.error}</p>
                    ) : (
                        <div className="text-sm text-muted-foreground space-y-1">
                            <p>HTTP {response.status_code} Error</p>
                            <p>
                                The request failed with status code {response.status_code}.
                                {response.status_code >= 500 && " This indicates a server error."}
                                {response.status_code >= 400 &&
                                    response.status_code < 500 &&
                                    " This indicates a client error."}
                            </p>
                        </div>
                    )}
                </div>
            )}

            <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">Request URL</p>
                <div className="text-sm font-mono bg-muted/50 p-3 rounded-md border break-all">
                    {response.request_url}
                </div>
            </div>

            {response.request_headers && Object.keys(response.request_headers).length > 0 && (
                <div>
                    <p className="text-sm font-medium text-muted-foreground mb-2">
                        Request Headers
                    </p>
                    <div className="bg-muted/50 p-3 rounded-md border">
                        <JSONViewer data={response.request_headers} className="max-h-32" />
                    </div>
                </div>
            )}

            {response.response_headers && Object.keys(response.response_headers).length > 0 && (
                <div>
                    <p className="text-sm font-medium text-muted-foreground mb-2">
                        Response Headers
                    </p>
                    <div className="bg-muted/50 p-3 rounded-md border">
                        <JSONViewer data={response.response_headers} className="max-h-32" />
                    </div>
                </div>
            )}

            <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">Response Body</p>
                <div className="bg-muted/50 p-3 rounded-md border">
                    <JSONViewer data={response.response_body} className="max-h-96" />
                </div>
            </div>
        </div>
    );
}
