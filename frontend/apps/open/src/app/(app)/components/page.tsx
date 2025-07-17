// Local imports
import { fetchComponents } from "@/lib/api";
import { ComponentsTable } from "./components-table";

export const dynamic = "force-dynamic";

export default async function Page() {
    const components = await fetchComponents().catch((error) => {
        console.error(error);
        return [];
    });

    return (
        <div className="flex flex-1 flex-col gap-6 p-4 lg:gap-6 lg:p-6">
            <div className="flex flex-col gap-4">
                <h1 className="text-lg font-semibold md:text-2xl">Components</h1>
                <div className="h-[1px] w-full bg-border" />
            </div>
            <div>
                <ComponentsTable components={components} />
            </div>
        </div>
    );
}
