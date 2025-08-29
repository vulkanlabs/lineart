import { fetchComponent } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@vulkanlabs/base/ui";
import { EnvTab } from "./components";
import { AppWorkflowFrame } from "@/components/workflow-frame";

export default async function Page(props: { params: Promise<{ component_name: string }> }) {
    const params = await props.params;
    const { component_name } = params;
    console.log("component_name", component_name);
    const component = await fetchComponent(component_name);

    if (!component) {
        return <div>Component not found</div>;
    }

    return (
        <div className="flex flex-col flex-1 p-6 h-full">
            <Tabs defaultValue="workflow" className="w-full h-full flex flex-col">
                <TabsList className="mb-4 w-fit">
                    <TabsTrigger value="workflow">Workflow</TabsTrigger>
                    <TabsTrigger value="env">Environment Variables</TabsTrigger>
                </TabsList>
                <TabsContent value="workflow" className="h-full flex-1">
                    <div className="w-full h-full">
                        <AppWorkflowFrame workflowData={component} />
                    </div>
                </TabsContent>
                <TabsContent value="env">
                    <EnvTab component={component} />
                </TabsContent>
            </Tabs>
        </div>
    );
}
