"use server";
import { Run } from "@vulkanlabs/client-open";
import { LauncherFnParams } from "./types";

export async function postLaunchFormAction({
    launchUrl,
    body,
    headers,
    label,
}: LauncherFnParams): Promise<Run> {
    return fetch(launchUrl, {
        method: "POST",
        headers: {
            ...headers,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        mode: "cors",
    })
        .then(async (response) => {
            if (!response.ok) {
                const responseBody = await response.json();
                if (responseBody?.detail && responseBody.detail?.msg) {
                    const errorMsg = responseBody.detail.msg
                        .replace("Failed to launch run: Failed to trigger job: ", "")
                        .replaceAll('"', '\\"')
                        .replaceAll("'", '"');
                    const splicedError = "[" + errorMsg.substring(1, errorMsg.length - 1) + "]";
                    const errorObj = JSON.parse(splicedError);
                    const errorObjAsString = JSON.stringify(errorObj, null, 2);

                    throw new Error(errorObjAsString);
                }

                throw new Error("Failed to create Run: " + JSON.stringify(responseBody, null, 2));
            }
            const data: Run = await response.json();
            return data;
        })
        .catch((error: any) => {
            const baseMsg = error.message || "An unknown error occurred";
            const errorMsg = label ? `${baseMsg}: ${label}` : baseMsg;
            throw new Error(errorMsg);
        });
}
