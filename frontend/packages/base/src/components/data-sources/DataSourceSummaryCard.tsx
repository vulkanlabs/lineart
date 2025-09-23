"use client";

import { CalendarIcon } from "lucide-react";
import type { DataSource } from "@vulkanlabs/client-open";
import { Card, CardContent, CardHeader, CardTitle, ScrollArea } from "../ui";

interface DataSourceSummaryCardProps {
    dataSource: DataSource;
    formatDate: (date: Date) => string;
    formatJson: (json: any) => string | null;
}

export function DataSourceSummaryCard({
    dataSource,
    formatDate,
    formatJson,
}: DataSourceSummaryCardProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <CalendarIcon className="h-5 w-5" />
                    Summary
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid gap-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <p className="text-sm font-medium">Created At</p>
                            <p className="text-sm text-muted-foreground">
                                {formatDate(dataSource.created_at)}
                            </p>
                        </div>
                        <div>
                            <p className="text-sm font-medium">Last Updated</p>
                            <p className="text-sm text-muted-foreground">
                                {formatDate(dataSource.last_updated_at)}
                            </p>
                        </div>
                    </div>
                    {dataSource.metadata && (
                        <div>
                            <p className="text-sm font-medium">Metadata</p>
                            <Card className="bg-muted/50 mt-2">
                                <CardContent className="p-4">
                                    <ScrollArea className="h-[150px]">
                                        <pre className="text-xs">
                                            {formatJson(dataSource.metadata)}
                                        </pre>
                                    </ScrollArea>
                                </CardContent>
                            </Card>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
