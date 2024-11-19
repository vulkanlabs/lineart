"use server";

export async function uploadFileFormAction({
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
    const request = new Request(uploadUrl, {
        method: "POST",
        headers: {
            ...headers,
        },
        body: body,
        mode: "cors",
    });

    return fetch(request)
        .then(async (response) => {
            if (!response.ok) {
                throw new Error("Failed to upload file: " + response, { cause: response });
            }
            const data = await response.json();
            return data;
        })
        .catch((error) => {
            const baseMsg = "Error fetching data";
            const errorMsg = label ? `${baseMsg}: ${label}` : baseMsg;
            throw new Error(errorMsg, {
                cause: error,
            });
        });
}
