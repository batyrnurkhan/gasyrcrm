/** @type {import('tailwindcss').Config} */
const defaultTheme = require('tailwindcss/defaultTheme')
const colors = require('tailwindcss/colors')

module.exports = {
    content: [
        "./core/**/*.{html,js}",
        "./users/**/*.{html,js}"
    ],
    theme: {
        extend: {},
        colors: {
            'black-main': "#4F4F4F",
            'accent-red': "#BA2025",
            black: colors.black,
            white: colors.white,
            gray: colors.gray,
            emerald: colors.emerald,
            indigo: colors.indigo,
            yellow: colors.yellow,
        },
        fontFamily: {
            "Qanelas": ['Qanelas', ...defaultTheme.fontFamily.sans],
        }
    },
    plugins: [],
}

