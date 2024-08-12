import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import { ChevronRight } from "lucide-react"

import { Button } from "@/components/ui/button";


export default function WorkflowSidebar({ clickedNode, closeFunc }) {

    function codeSnippet(clickedNode) {
        if (clickedNode.data.hasOwnProperty("source")) {
            return (
                <div className="my-5 pr-10">
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
            <div className="flex flex-row my-2">
                <h1 className="text-lg font-semibold w-[10em]">{name}</h1>
                <p>{value}</p>
            </div>
        );
    }

    return (
        <div className="h-full bg-white border-l-2">
            <div className="flex items-right">
                <Button variant="outline" size="icon" onClick={closeFunc}>
                    <ChevronRight className="h-4 w-4" />
                </Button>
            </div>
            <div className="flex flex-col px-5 mt-5">
                <div>
                    <NodeParam name={"Nome"} value={clickedNode.data.label} />
                    <NodeParam name={"Tipo"} value={clickedNode.data.type} />
                    <NodeParam name={"Descrição"} value={clickedNode.data.description} />
                </div>
                {codeSnippet(clickedNode)}
            </div>
        </div>
    );
}