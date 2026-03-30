/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./node_modules/@heroui/react/dist/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        bg: '#f4ecdf',
        panel: 'rgba(255, 249, 240, 0.92)',
        'panel-strong': '#fffdf8',
        text: '#1f2a33',
        muted: '#6d7468',
        accent: '#0d7c6c',
        'accent-strong': '#0b5f54',
        'accent-soft': '#d7f1ea',
        'accent-warm': '#f1c97f',
        border: 'rgba(96, 82, 62, 0.18)'
      },
      fontFamily: {
        serif: ['Iowan Old Style', 'Palatino Linotype', 'serif'],
        sans: ['Avenir Next', 'Segoe UI', 'sans-serif']
      },
      borderRadius: {
        '4xl': '2rem'
      }
    }
  },
  plugins: []
}
