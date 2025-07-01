import type { Metadata } from 'next'
import '@vulkan/base/src/styles/globals.css'

export const metadata: Metadata = {
  title: 'Vulkan Engine',
  description: 'An easy-to-use, fully featured console to manage your policies.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}