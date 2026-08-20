import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        tavaura: {
          white: "#ffffff",
          ink: "#1f353c",
          cocoa: "#3c261f",
          bg: "#f5f7f8",
          accent: "#3c261f"
        }
      },
      boxShadow: {
        tavaura: "0 8px 24px rgba(0, 0, 0, 0.06)", // Primary soft elevation
        "tavaura-lg": "0 12px 32px rgba(0, 0, 0, 0.08)", // For modals/overlays
        "tavaura-sm": "0 4px 12px rgba(0, 0, 0, 0.04)" // For subtle cards
      }
    }
  },
  plugins: []
};



export default config;
