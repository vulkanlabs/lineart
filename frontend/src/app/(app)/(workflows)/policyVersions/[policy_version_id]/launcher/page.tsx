"use client";
import { useEffect, useState } from "react";
import { LaunchRunForm } from "./components";
import { useUser } from "@stackframe/stack";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { CardContent } from "@mui/material";

export default function Page({ params }) {
    const user = useUser();
    const [createdRun, setCreatedRun] = useState(null);
    const [error, setError] = useState<Error>(null);

    useEffect(() => {}, [createdRun, error]);

    return (
        <div className="flex flex-col p-8 gap-8">
            <h1 className="text-2xl font-bold tracking-tight">Launch a Run</h1>
            <div>
                <LaunchRunForm
                    user={user}
                    policy_version_id={params.policy_version_id}
                    setCreatedRun={setCreatedRun}
                    setError={setError}
                />
            </div>
            {createdRun && <RunCreatedCard createdRun={createdRun} />}
            {error && <RunCreationErrorCard error={error} />}
        </div>
    );
}

function RunCreatedCard({ createdRun }) {
    return (
        <Card className="flex flex-col w-fit border-green-600 border-2">
            <CardHeader>
                <CardTitle>Launched run successfully</CardTitle>
                <CardDescription>
                    <Link href={`/runs/${createdRun.run_id}`}>
                        <Button className="bg-green-600 hover:bg-green-500">View Run</Button>
                    </Link>
                </CardDescription>
            </CardHeader>
        </Card>
    );
}

function RunCreationErrorCard({ error }) {
    console.log(error);
    return (
        <Card className="flex flex-col w-fit items-center border-red-600 border-2">
            <CardHeader>
                <CardTitle>Failed to launch run</CardTitle>
                <CardDescription>
                    Launch failed with error: <br />
                </CardDescription>
            </CardHeader>
            <CardContent>
                <pre>{error.message}</pre>
            </CardContent>
        </Card>
    );
}
