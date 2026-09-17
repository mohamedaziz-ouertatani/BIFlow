import type { Metadata } from "next";
import { Geist, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "BIFlow",
  description: "Automated BI pipeline powered by 7 collaborative agents",
};

// Root HTML shell applied to every page, wiring up the Geist and IBM Plex Mono fonts.
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${plexMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
