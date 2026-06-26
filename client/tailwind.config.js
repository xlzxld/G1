/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class', // Enable class-based dark mode
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          900: '#1a1b26', // Deep dark background
          800: '#24283b', // Card/Bento background
          700: '#414868', // Borders and accents
          border: '#3b4261', // Specific border color
          accent: '#7aa2f7', // Tech blue accent
          orange: '#ff9e64', // Warning/highlight orange
        }
      }
    },
  },
  plugins: [],
}
