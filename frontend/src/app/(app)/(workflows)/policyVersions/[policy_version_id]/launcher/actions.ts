"use server";
export async function postLaunchFormAction({
    launchUrl,
    body,
    headers,
    label,
}: {
    launchUrl: string;
    body: any,
    headers: any,
    label?: string;
}) {

    return fetch(launchUrl, {
        method: "POST",
        headers: {
            ...headers,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body),
        mode: "cors",
    })
        .then(async (response) => {
            if (!response.ok) {
                const responseBody = await response.json();
                if (responseBody?.detail && responseBody.detail?.msg) {
                    const errorMsg = responseBody.detail.msg.replace(
                        "Failed to launch run: Failed to trigger job: ",
                        "",
                    ).replaceAll('"', '\\"').replaceAll("'", '"');
                    const splicedError = "[" + errorMsg.substring(1, errorMsg.length - 1) + "]";
                    const errorObj = JSON.parse(splicedError);
                    const errorObjAsString = JSON.stringify(errorObj, null, 2);

                    throw new Error(errorObjAsString);
                }

                throw new Error("Failed to create Run: " + response, { cause: response });
            }
            const data = await response.json();
            return data
        })
        .catch((error) => {
            const baseMsg = "Error fetching data";
            const errorMsg = label ? `${baseMsg}: ${label}` : baseMsg;
            throw new Error(errorMsg, {
                cause: error,
            });
        });
}