import { FileUploaderPage } from "./components";
import { getAuthHeaders } from "@/lib/auth";

export default async function Page(props) {
    const params = await props.params;
    return (
        <FileUploaderPage
            uploadFn={uploadFileFormAction}
            policyVersionId={params.policy_version_id}
        />
    );
}

async function uploadFileFormAction({
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
