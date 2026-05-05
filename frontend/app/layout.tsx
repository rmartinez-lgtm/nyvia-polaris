import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nyvia Brain",
  description: "Base de conocimiento interna de Nyvia",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
