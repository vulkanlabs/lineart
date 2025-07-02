import { defineConfig } from 'tsup'
import path from 'path'

import fs from 'fs'

export default defineConfig({
  entry: ['src/index.ts', 'src/ui/index.ts'],
  format: ['cjs', 'esm'],
  dts: false, // Disabled due to chart component type errors
  clean: true,
  external: ['react', 'react-dom', 'next'],
  splitting: false,
  minify: false,
  outDir: 'dist',
  treeshake: true,
  esbuildOptions(options) {
    options.alias = {
      '@': path.resolve(process.cwd(), 'src')
    }
    options.jsx = 'transform'
    options.jsxFactory = 'React.createElement'
    options.jsxFragment = 'React.Fragment'
    options.inject = [path.resolve(__dirname, 'react-shim.js')]
  },
  onSuccess: async () => {
    // Add "use client" directive to all built files
    const files = ['dist/index.js', 'dist/index.mjs', 'dist/ui/index.js', 'dist/ui/index.mjs']
    for (const file of files) {
      if (fs.existsSync(file)) {
        const content = fs.readFileSync(file, 'utf8')
        if (!content.startsWith('"use client";')) {
          fs.writeFileSync(file, '"use client";\n' + content)
        }
      }
    }
    console.log('Build completed successfully!')
  }
})