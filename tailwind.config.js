/** @type {import('tailwindcss').Config} */
const defaultTheme = require('tailwindcss/defaultTheme')
const colors = require('tailwindcss/colors')
/* Tailwind command:
npm install -D tailwindcss
npx tailwindcss -i .\core\static\core\css\input.css -o .\core\static\core\css\output.css --watch
*/
module.exports = {
    content: [
        "./core/**/*.{html,js}",
        "./users/**/*.{html,js}",
        "./courses/**/*.{html,js}",
    ],
    theme: {
        extend: {},
        colors: {
            'black-main': "#4F4F4F",
            'accent-red': "#BA2025",
            'light-gray': "rgba(246, 246, 246, 1)",
            gray: "rgba(194, 194, 194, 1)",
            green: "rgba(90, 180, 34, 1)",
            'math': "rgba(80, 181, 33, 1)",
            'blue-ielts': "rgba(122, 72, 228, 1)",
            whiteless: "rgba(250, 250, 250, 1)",
            black: colors.black,
            white: colors.white,
            emerald: colors.emerald,
            indigo: colors.indigo,
            yellow: colors.yellow,
        },
        fontFamily: {
            "Qanelas": ['Qanelas', ...defaultTheme.fontFamily.sans],
        },
    },
    plugins: [],
}

