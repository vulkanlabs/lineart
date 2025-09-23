"use client";

import type { DataSource } from "@vulkanlabs/client-open";
import { Card, CardContent, CardHeader, CardTitle } from "../ui";

interface RetryPolicyCardProps {
    dataSource: DataSource;
}

export function RetryPolicyCard({ dataSource }: RetryPolicyCardProps) {
    if (!dataSource.source.retry) {
        return null;
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-base">Retry Policy</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-3 gap-4">
                    <div>
                        <p className="text-sm font-medium">Max Retries</p>
                        <p className="text-sm text-muted-foreground">
                            {dataSource.source.retry.max_retries}
                        </p>
                    </div>
                    <div>
                        <p className="text-sm font-medium">Backoff Factor</p>
                        <p className="text-sm text-muted-foreground">
                            {dataSource.source.retry.backoff_factor}
                        </p>
                    </div>
                    <div>
                        <p className="text-sm font-medium">Status Force List</p>
                        <p className="text-sm text-muted-foreground">
                            {dataSource.source.retry.status_forcelist
                                ? dataSource.source.retry.status_forcelist.join(", ")
                                : "None"}
                        </p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
