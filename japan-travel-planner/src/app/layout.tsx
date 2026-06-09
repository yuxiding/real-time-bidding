import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { DarkModeProvider } from "@/components/DarkModeProvider";
import Navigation from "@/components/Navigation";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Japan Travel Planner – AI-Powered Itineraries",
  description: "Plan your perfect Japan trip with AI. Get personalized day-by-day itineraries, hotel recommendations, and budget breakdowns.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors">
        <DarkModeProvider>
          <Navigation />
          <main className="flex-1">{children}</main>
          <footer className="border-t border-gray-200 dark:border-gray-800 py-6 text-center text-sm text-gray-500 dark:text-gray-400">
            © 2025 Japan Travel Planner · Built with AI
          </footer>
        </DarkModeProvider>
      </body>
    </html>
  );
}
