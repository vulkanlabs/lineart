import { stackServerApp } from "@/stack";

import { fetchBacktestFiles } from "@/lib/api";
import { BacktestLauncherPage } from "./components";

export default async function Page({ params }) {
    const user = await stackServerApp.getUser();
    const uploadedFiles = await fetchBacktestFiles(user, params.policy_version_id).catch(
        (error) => {
            console.error(error);
            return [];
        },
    );
    return (
        <BacktestLauncherPage
            launchFn={launchBacktestFormAction}
            uploadedFiles={uploadedFiles}
            policyVersionId={params.policy_version_id}
        />
    );
}

export async function launchBacktestFormAction({
    uploadUrl,
    body,
    headers,
    label,
}: {
    uploadUrl: string;
    body: any;
    headers: any;
    label?: string;
}) {
    "use server";

    const request = new Request(uploadUrl, {
        method: "POST",
        headers: {
            ...headers,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        mode: "cors",
    });

    return fetch(request)
        .then(async (response) => {
            if (!response.ok) {
                throw new Error("Failed to launch backtest: " + response, { cause: response });
            }
            const data = await response.json();
            return data;
        })
        .catch((error) => {
            const baseMsg = "Error launching backtest";
            const errorMsg = label ? `${baseMsg}: ${label}` : baseMsg;
            throw new Error(errorMsg, {
                cause: error,
            });
        });
}
