import { defineConfig } from "tsup";
import path from "path";
import fs from "fs";
import { glob } from "glob";

export default defineConfig(async () => {
    // Automatically discover all entry points
    const entryPoints = [
        // Main entry points
        "src/index.ts",
        "src/ui/index.ts",
        "src/workflow/index.ts",

        // Feature-based entry points
        "src/components/*/index.ts",

        // Individual utilities that need server compatibility
        "src/lib/api/api-utils.ts",
        "src/lib/utils.ts",
        "src/lib/chart.ts",
    ];

    // Resolve glob patterns to actual files
    const resolvedEntries: string[] = [];
    for (const pattern of entryPoints) {
        if (pattern.includes("*")) {
            const matches = await glob(pattern, { cwd: process.cwd() });
            resolvedEntries.push(...matches);
        } else {
            resolvedEntries.push(pattern);
        }
    }

    return {
        entry: resolvedEntries,
        format: ["cjs", "esm"],
        dts: true, // Enable TypeScript declarations
        clean: true,
        external: ["react", "react-dom", "next"],
        splitting: true,
        minify: false,
        treeshake: true,
        outDir: "dist",

        esbuildOptions(options) {
            options.alias = {
                "@": path.resolve(process.cwd(), "src"),
                "@vulkanlabs/base": path.resolve(process.cwd(), "src/index.ts"),
                "@vulkanlabs/base/ui": path.resolve(process.cwd(), "src/ui/index.ts"),
                "@vulkanlabs/base/workflow": path.resolve(process.cwd(), "src/workflow/index.ts"),
            };
            options.jsx = "transform";
            options.jsxFactory = "React.createElement";
            options.jsxFragment = "React.Fragment";
            options.inject = [path.resolve(__dirname, "react-shim.js")];
        },

        onSuccess: async () => {
            // Add "use client" directive to client-only files
            const clientFiles = await glob("dist/**/index.{js,mjs}", {
                ignore: ["**/api-utils.*", "**/utils.*", "**/chart.*"],
            });

            for (const file of clientFiles) {
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
            if (fs.existsSync("src/styles/globals.css")) {
                fs.copyFileSync("src/styles/globals.css", "dist/styles/globals.css");
            }

            console.log("✅ Build completed successfully!");
            console.log(`📦 Built ${resolvedEntries.length} entry points`);
        },
    };
});
