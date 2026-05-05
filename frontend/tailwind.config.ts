import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        nyvia: {
          dark: "#0F1117",
          surface: "#1A1D27",
          border: "#2A2D3A",
          accent: "#00BDA3",
          text: "#E2E8F0",
          muted: "#718096",
        },
      },
    },
  },
  plugins: [],
};

export default config;
