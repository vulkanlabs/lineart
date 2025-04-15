import { fetchComponents } from "@/lib/api";
import ComponentPageContent from "./components";

export default async function Page() {
    const components = await fetchComponents().catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <div className="flex flex-1 flex-col gap-4 p-4 lg:gap-6 lg:p-6">
            <div className="flex items-center">
                <h1 className="text-lg font-semibold md:text-2xl">Components</h1>
            </div>
            <ComponentPageContent components={components} />
        </div>
    );
}
