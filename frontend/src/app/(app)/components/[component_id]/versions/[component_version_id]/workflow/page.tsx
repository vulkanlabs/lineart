import WorkflowPage from "@/components/workflow/workflow";
import { fetchComponentVersion } from "@/lib/api";

export default async function Page(props) {
    const params = await props.params;
    const graphData = await fetchComponentVersion(params.component_version_id)
        .then((data) => {
            return JSON.parse(data["node_definitions"]);
        })
        .catch((error) => {
            console.error(error);
            return null;
        });
    // TODO: temporary fix to add input node (ComponentDefinition doesn't have
    // an internally inserted input node).
    graphData["input_node"] = {
        name: "input_node",
        node_type: "INPUT",
        hidden: false,
        description: "Input node",
        dependencies: null,
        metadata: {},
    };

    return <WorkflowPage graphData={graphData} />;
}
