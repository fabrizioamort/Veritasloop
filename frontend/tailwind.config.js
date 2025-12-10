/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'accent': 'var(--color-accent)',
                'pro': 'var(--color-pro)',
                'contra': 'var(--color-contra)',
                'judge': 'var(--color-judge)',
            },
            fontFamily: {
                'main': ['Inter', 'system-ui', 'sans-serif'],
                'mono': ['JetBrains Mono', 'monospace'],
            },
        },
    },
    plugins: [],
}
