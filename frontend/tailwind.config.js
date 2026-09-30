/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        canvas: "#f5f7fb",
        brand: {
          50: "#eef4ff",
          100: "#dce8ff",
          500: "#356ae6",
          600: "#2857c8",
          700: "#2349a5"
        }
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.04)"
      }
    }
  },
  plugins: []
};
