import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Tavaura — giving aura to your avatar",
  description:
    "Virtual try-on for fashion and cosmetics, embeddable on any online store.",
  openGraph: {
    title: "Tavaura — virtual try-on for fashion and cosmetics",
    description:
      "Let shoppers try outfits and looks on avatars or photos, right inside your store.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        suppressHydrationWarning
        className={`${geistSans.variable} ${geistMono.variable} bg-tavaura-bg text-tavaura-ink antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
