import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'DI AI Insider Dashboard',
  description: 'Dynamic Marketing Dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="layout-container">
          {/* Sidebar will go here */}
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
