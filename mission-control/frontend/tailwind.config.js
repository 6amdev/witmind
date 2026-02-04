/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Background
        'bg-primary': '#0d1117',
        'bg-secondary': '#161b22',
        'bg-tertiary': '#21262d',
        'bg-elevated': '#30363d',
        // Border
        'border-default': '#30363d',
        'border-muted': '#21262d',
        // Text
        'text-primary': '#f0f6fc',
        'text-secondary': '#8b949e',
        'text-muted': '#6e7681',
        // Accent
        'accent-blue': '#58a6ff',
        'accent-green': '#3fb950',
        'accent-yellow': '#d29922',
        'accent-red': '#f85149',
        'accent-purple': '#a371f7',
        'accent-orange': '#f0883e',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 250ms ease-out',
        'slide-up': 'slideUp 250ms ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
