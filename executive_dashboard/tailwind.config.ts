import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}", "./lib/**/*.{js,ts,jsx,tsx}", "./tests/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#002c6e",
        skyline: "#dbe8ff",
        mist: "#f5f8ff",
        steel: "#eef2f7",
        citrus: "#f0a45a",
      },
      boxShadow: {
        panel: "0 18px 45px rgba(15, 38, 92, 0.10)",
      },
      borderRadius: {
        panel: "0.75rem",
      },
      fontFamily: {
        sans: ["ITC Avant Garde", "Avenir Next", "Trebuchet MS", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
