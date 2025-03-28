import { useCallback, useState } from "react";

import { useShallow } from "zustand/react/shallow";
import Editor from "@monaco-editor/react";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

import { useWorkflowStore } from "../store";
import { WorkflowNode } from "./base";

const CodeEditorWindow = ({ onChange, language, code, theme, height, width }) => {
    const [value, setValue] = useState(code || "");

    const handleEditorChange = (value) => {
        setValue(value);
        onChange("code", value);
    };

    return (
        // <div className="rounded-md overflow-hidden m-3">
        <Editor
            // height={height}
            // width={width}
            language={language || "javascript"}
            value={value}
            theme={theme}
            defaultValue="// some comment"
            onChange={handleEditorChange}
        />
        // </div>
    );
};

export function TransformNode({ id, data, selected, height, width }) {
    const [code, setCode] = useState("");

    return (
        <WorkflowNode id={id} selected={selected} data={data} height={height} width={width}>
            {/* <CodeEditorWindow
                onChange={() => {}}
                language="javascript"
                code={""}
                theme="vs-dark"
                height={height}
                width={width}
            /> */}
            <Textarea value={code} onChange={(e) => setCode(e.target.value)} />
        </WorkflowNode>
    );
}
