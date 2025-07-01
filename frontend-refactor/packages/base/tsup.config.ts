import { defineConfig } from 'tsup'

export default defineConfig({
  entry: ['src/index.ts', 'src/ui/index.ts'],
  format: ['cjs', 'esm'],
  dts: true,
  clean: true,
  external: ['react', 'react-dom', 'next'],
  splitting: false,
  minify: false,
  outDir: 'dist',
  treeshake: true
})