"use client";

import { CheckCircle, XCircle, Clock, Database } from "lucide-react";
import { Badge, Card, CardContent, CardHeader, CardTitle, Separator } from "../ui";
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
 * Right panel component displaying test response data
 * Shows status, headers, response time, and response body
 */
export function TestResponsePanel({ response, isLoading }: TestResponsePanelProps) {
    if (isLoading)
        return (
            <Card className="h-full">
                <CardHeader>
                    <CardTitle>Response</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-64">
                        <div className="text-muted-foreground">Testing...</div>
                    </div>
                </CardContent>
            </Card>
        );

    if (!response)
        return (
            <Card className="h-full">
                <CardHeader>
                    <CardTitle>Response</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center h-64">
                        <div className="text-muted-foreground">
                            Configure and run a test to see the response
                        </div>
                    </div>
                </CardContent>
            </Card>
        );

    const isSuccess = response.status_code >= 200 && response.status_code < 300;
    const isError = response.status_code >= 400 || response.status_code === 0;

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle className="flex items-center justify-between">
                    <span>Response</span>
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
                                {response.status_code === 0 ? "Network Error" : "Error"}
                            </Badge>
                        )}
                    </div>
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">Status Code</div>
                        <div className="text-lg font-semibold">
                            {response.status_code === 0 ? "Network Error" : response.status_code}
                        </div>
                    </div>
                    <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            Response Time
                        </div>
                        <div className="text-lg font-semibold">{response.response_time_ms}ms</div>
                    </div>
                </div>

                {response.cache_hit && (
                    <div className="flex items-center gap-2 text-sm text-blue-600">
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

                <Separator />

                <div className="space-y-1">
                    <div className="text-sm font-medium text-muted-foreground">Request URL</div>
                    <div className="text-sm font-mono bg-muted p-2 rounded-md break-all">
                        {response.request_url}
                    </div>
                </div>

                <Separator />

                <div className="space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">
                        Response Headers
                    </div>
                    <JSONViewer data={response.headers} className="max-h-32" />
                </div>

                <Separator />

                <div className="space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">Response Body</div>
                    <JSONViewer data={response.response_body} className="max-h-96" />
                </div>
            </CardContent>
        </Card>
    );
}
