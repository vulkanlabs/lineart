import { defineConfig } from "tsup";
import path from "path";

import fs from "fs";

export default defineConfig({
    entry: [
        "src/index.ts",
        "src/ui/index.ts",
        "src/workflow/index.ts",
        "src/lib/api/api-utils.ts", // Separate entry for server-compatible API utils
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
    dts: false, // Disabled due to lazy loading compatibility issues with generics
    clean: true,
    external: ["react", "react-dom", "next"],
    splitting: true, // Enable code splitting for better load performance and caching
    minify: false,
    treeshake: true, // Remove unused code for optimal bundle size

    outDir: "dist",
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
        // Add "use client" directive to client-only built files (NOT api-utils)
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

        // Copy styles to dist
        const stylesDir = "dist/styles";
        if (!fs.existsSync(stylesDir)) {
            fs.mkdirSync(stylesDir, { recursive: true });
        }
        fs.copyFileSync("src/styles/globals.css", "dist/styles/globals.css");

        console.log("Build completed successfully!");
    },
});
