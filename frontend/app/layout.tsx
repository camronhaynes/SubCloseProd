import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Late Interest Calculator - Test Interface',
  description: 'Test interface for the Late Interest Engine',
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
