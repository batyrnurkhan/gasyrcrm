/** @type {import('tailwindcss').Config} */
const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  content: ["./core/**/*.{html,js}"],
  theme: {
    extend: {},
    colors: {
      'black-main': "#4F4F4F",
      'accent-red': "#BA2025"
    },
    fontFamily: {
      "Qanelas": ['Qanelas', ...defaultTheme.fontFamily.sans],
    }
  },
  plugins: [],
}

