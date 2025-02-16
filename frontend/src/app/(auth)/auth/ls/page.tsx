import { stackServerApp } from "@/stack";
import { getUserProjectId } from "@/lib/api";

// Return the user's project and User ID as a JSON object
export default async function Page() {
    const user = await stackServerApp.getUser();
    if (!user) {
        return null;
    }

    const projectId = await getUserProjectId(user);
    return (
        <div>
            <pre>{JSON.stringify(projectId, null, 2)}</pre>
        </div>
    );
}
