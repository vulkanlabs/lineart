"use client";

import { Settings2Icon } from "lucide-react";
import { Badge, Card, CardContent, CardHeader, CardTitle } from "@vulkanlabs/base/ui";
import type { DataSource } from "@vulkanlabs/client-open";

interface CachingConfigurationCardProps {
    dataSource: DataSource;
    formatTimeFromSeconds: (seconds: number) => string;
}

export function CachingConfigurationCard({
    dataSource,
    formatTimeFromSeconds,
}: CachingConfigurationCardProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Settings2Icon className="h-5 w-5" />
                    Caching Configuration
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid gap-4">
                    <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">Caching Enabled</p>
                        <Badge variant={dataSource.caching?.enabled ? "default" : "outline"}>
                            {dataSource.caching?.enabled ? "Enabled" : "Disabled"}
                        </Badge>
                    </div>

                    {dataSource.caching?.enabled && dataSource.caching?.ttl && (
                        <div>
                            <p className="text-sm font-medium">TTL (Time to Live)</p>
                            <p className="text-sm text-muted-foreground">
                                {formatTimeFromSeconds(Number(dataSource.caching.ttl))} (
                                {Number(dataSource.caching.ttl)} seconds)
                            </p>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
