import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';


function codeSnippet(clickedNode) {
    if (clickedNode.data.hasOwnProperty("source")) {
        return (
            <div className="my-5">
                <h1 className="text-lg font-semibold">Source Code</h1>
                <div className="mt-3 rounded overflow-auto">
                    <SyntaxHighlighter language="python" style={atomOneDark}>
                        {clickedNode.data.source}
                    </SyntaxHighlighter>
                </div>
            </div>
        );
    }
    return null;
}


function NodeParam({ name, value }) {
    return (
        <div className="grid grid-cols-4 my-2">
            <div className="col-span-2 text-lg font-normal">{name}</div>
            <div className="col-span-2 overflow-scroll">{value}</div>
        </div>
    );
}


function NodeContent({ clickedNode }) {
    if (clickedNode.length === 0) {
        return (
            <div className="flex flex-col px-5">
                <h1 className="mt-5 text-lg font-semibold">No node selected</h1>
            </div>
        );
    }

    return (
        <div className="flex flex-col px-5">
            <div className="mt-5">
                <NodeParam name={"Name"} value={clickedNode.data.label} />
                <NodeParam name={"Type"} value={clickedNode.data.type} />
                <NodeParam name={"Description"} value={clickedNode.data.description} />
            </div>
            {codeSnippet(clickedNode)}
            {clickedNode.parentId && (
                <div className="mt-5">
                    <h1 className="text-lg font-semibold">Component</h1>
                    <div className="mt-3">
                        <NodeParam name={"Instance"} value={clickedNode.parentId} />
                        <NodeParam name={"Reference"} value={clickedNode.parentReference} />
                    </div>
                </div>
            )}
        </div>
    );
}


export default function WorkflowSidebar({ clickedNode }) {
    return (
        <div className="h-full bg-white border-l-2">
            <NodeContent clickedNode={clickedNode} />
        </div>
    );
}