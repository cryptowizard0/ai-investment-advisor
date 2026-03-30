import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./lib/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#070b11",
          900: "#0d131b",
          800: "#121a24",
          700: "#1d2835",
          500: "#7890ab",
          300: "#c3d4e7",
          200: "#dce6f2"
        },
        accent: {
          500: "#77e0c6",
          400: "#9af0da"
        },
        alert: {
          500: "#f5a26f"
        }
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"]
      },
      boxShadow: {
        panel: "0 24px 80px rgba(0, 0, 0, 0.35)"
      }
    },
  },
  plugins: [],
};

export default config;
