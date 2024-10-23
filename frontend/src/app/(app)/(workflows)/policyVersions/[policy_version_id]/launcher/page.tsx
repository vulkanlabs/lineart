"use client";
import { useState } from "react";
import { LaunchRunForm } from "./components";
import { useUser } from "@stackframe/stack";
import Link from "next/link";

export default function Page({ params }) {
    const user = useUser();
    const [createdRun, setCreatedRun] = useState(null);
    const [error, setError] = useState(null);

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
                {createdRun && (
                    <div>
                        <div className="flex flex-row gap-4">
                            <h2>Run successfully launched:</h2>
                            <a href={`/runs/${createdRun.run_id}`}>
                                <p className="">Run ID: {createdRun.run_id}</p>
                            </a>
                        </div>
                        <pre>{JSON.stringify(createdRun, null, 2)}</pre>
                    </div>
                )}
                {error && (
                    <div>
                        <h2>Failed to launch run:</h2>
                        <pre>{JSON.stringify(error, null, 2)}</pre>
                    </div>
                )}
            </div>
        </div>
    );
}
