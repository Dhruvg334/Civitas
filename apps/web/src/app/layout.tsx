import type { Metadata } from "next";
import "./globals.css";
import "./refinements.css";

export const metadata: Metadata = {
  title: "Civitas",
  description: "Turning every civic report into clear, accountable action.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
