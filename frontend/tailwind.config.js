/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        shield: {
          bg: "#101114",         // Exact Main background
          surface: "#3B3F46",    // Exact Surface
          primary: "#D9B100",    // Exact Primary accent
          soft: "#F3DA87",       // Exact Soft accent
          text: "#F2F4F6",       // Exact Primary text
          // Cohesive dark cybersecurity tints
          base: "#14161A",
          card: "#191C22",
          elevated: "#21252D",
          border: "#2C313C",
          hover: "#2A2F3A",
          muted: "#949BA6",
          subtle: "#626A77",
          // Security Status Badges
          success: "#10B981",
          warning: "#F59E0B",
          danger: "#EF4444",
          info: "#38BDF8",
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
