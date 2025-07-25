import { defineConfig } from "tsup";
import path from "path";

import fs from "fs";

export default defineConfig({
    entry: [
        "src/index.ts",
        "src/ui/index.ts",
        "src/workflow/index.ts",
        // Add individual component entries for proper TypeScript declarations
        "src/components/details-button.tsx",
        "src/components/shortened-id.tsx",
        "src/components/resource-table.tsx",
        "src/components/data-table.tsx",
        "src/components/combobox.tsx",
        "src/components/component/index.tsx",
        "src/components/charts/index.tsx",
        "src/components/animations/index.tsx",
        "src/components/environment-variables-editor.tsx",
        "src/components/reactflow/index.tsx",
        "src/components/logo.tsx",
        "src/lib/utils.ts",
        "src/lib/chart.ts",
    ],
    format: ["cjs", "esm"],
    dts: true, // Re-enabled - we'll focus on core components first
    clean: true,
    external: ["react", "react-dom", "next"],
    splitting: false,
    minify: false,
    outDir: "dist",
    treeshake: true,
    esbuildOptions(options) {
        options.alias = {
            "@": path.resolve(process.cwd(), "src"),
            "@vulkanlabs/base/ui": path.resolve(process.cwd(), "src/ui/index.ts"),
            "@vulkanlabs/base/workflow": path.resolve(process.cwd(), "src/workflow/index.ts"),
            "@vulkanlabs/base": path.resolve(process.cwd(), "src/index.ts"),
        };
        options.jsx = "transform";
        options.jsxFactory = "React.createElement";
        options.jsxFragment = "React.Fragment";
        options.inject = [path.resolve(__dirname, "react-shim.js")];
    },
    onSuccess: async () => {
        // Add "use client" directive to all built files
        const files = [
            "dist/index.js",
            "dist/index.mjs",
            "dist/ui/index.js",
            "dist/ui/index.mjs",
            "dist/workflow/index.js",
            "dist/workflow/index.mjs",
        ];
        for (const file of files) {
            if (fs.existsSync(file)) {
                const content = fs.readFileSync(file, "utf8");
                if (!content.startsWith('"use client";')) {
                    fs.writeFileSync(file, '"use client";\n' + content);
                }
            }
        }
        console.log("Build completed successfully!");
    },
});
