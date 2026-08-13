import type { Metadata, Viewport } from "next";
import "./globals.css";
import "./refinements.css";

export const viewport: Viewport = {
  themeColor: "#0a0e17",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export const metadata: Metadata = {
  metadataBase: new URL("https://civitas.civic.local"),
  title: {
    default: "Civitas — Multimodal Civic Incident Intelligence",
    template: "%s | Civitas",
  },
  description:
    "Evidence-backed civic incident intelligence and resolution platform turning multimodal citizen reports into grounded municipal action.",
  keywords: [
    "civic intelligence",
    "incident resolution",
    "multimodal AI",
    "municipal operations",
    "pothole detection",
    "water leakage",
    "work order routing",
    "LangGraph",
  ],
  authors: [{ name: "Civitas Core Team" }],
  openGraph: {
    title: "Civitas — Multimodal Civic Incident Intelligence",
    description:
      "Turning citizen-submitted photographs, videos, descriptions, and GPS coordinates into policy-grounded municipal work orders.",
    url: "https://civitas.civic.local",
    siteName: "Civitas Intelligence Platform",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Civitas — Multimodal Civic Incident Intelligence",
    description:
      "Evidence-backed civic incident intelligence platform for municipal operations.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
