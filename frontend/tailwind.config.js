/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                border: "var(--border-color)",
                // We can add custom colors here if needed to map CSS vars to Tailwind
            },
            fontFamily: {
                sans: ['var(--font-sans)'],
                mono: ['var(--font-mono)'],
            }
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
