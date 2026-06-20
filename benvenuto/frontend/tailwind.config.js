/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: { italy: { green: "#008C45", white: "#F4F5F0", red: "#CD212A" } },
    },
  },
  plugins: [],
};
