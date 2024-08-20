import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { ChevronRight } from "lucide-react"

import { Button } from "@/components/ui/button";


function codeSnippet(clickedNode) {
    if (clickedNode.data.hasOwnProperty("source")) {
        return (
            <div className="my-5">
                <h1 className="text-lg font-semibold">Código</h1>
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
            {/* <h1 className="text-lg font-semibold w-[10em]">{name}</h1> */}
            <div className="col-span-2 text-lg font-semibold">{name}</div>
            <div className="col-span-2">{value}</div>
        </div>
    );
}


function NodeContent({ clickedNode }) {
    if (clickedNode.length === 0) {
        return (
            <div className="flex flex-col px-5">
                <h1 className="mt-5 text-lg font-semibold">Nenhum nó selecionado</h1>
            </div>
        );
    }

    return (
        <div className="flex flex-col px-5">
            <div className="mt-5">
                <NodeParam name={"Nome"} value={clickedNode.data.label} />
                <NodeParam name={"Tipo"} value={clickedNode.data.type} />
                <NodeParam name={"Descrição"} value={clickedNode.data.description} />
            </div>
            {codeSnippet(clickedNode)}
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