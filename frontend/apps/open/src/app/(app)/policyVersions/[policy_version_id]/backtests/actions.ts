"use server";

export async function workspaceCreationAction({ url, headers }: { url: string; headers: any }) {
    const request = new Request(url, {
        method: "POST",
        headers: {
            ...headers,
        },
        mode: "cors",
    });

    return fetch(request)
        .then(async (response) => {
            if (!response.ok) {
                throw new Error("Failed to create workspace: " + response, { cause: response });
            }
            const data = await response.json();
            return data;
        })
        .catch((error) => {
            const errorMsg = "Error creating workspace";
            throw new Error(errorMsg, {
                cause: error,
            });
        });
}
