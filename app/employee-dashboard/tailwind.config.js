/**** @type {import('tailwindcss').Config} ****/
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        dunkin: {
          orange: "#FF671F",
          pink: "#E3007F",
          sand: "#FFEBD2",
          cocoa: "#7A2E10"
        }
      }
    }
  },
  plugins: []
};
