/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: {
          bg: '#080D0B',
          sidebar: '#0B110E',
          card: '#101914',
          panel: '#142019',
          hover: '#1C2D24',
          border: '#263A2E',
          'text-primary': '#F0F7F2',
          'text-secondary': '#A0B2A6',
          'text-muted': '#718278',
        },
        jade: {
          DEFAULT: '#55E6A5',
          hover: '#35D993',
          glow: 'rgba(85, 230, 165, 0.25)',
        },
        amber: {
          DEFAULT: '#FFC66D',
          hover: '#F5B752',
          glow: 'rgba(255, 198, 109, 0.25)',
        },
        iris: {
          DEFAULT: '#A99BFF',
          hover: '#9382FF',
          glow: 'rgba(169, 155, 255, 0.25)',
        },
        status: {
          running: '#7AB8FF',
          error: '#FF7777',
          success: '#55E6A5',
          approval: '#FFC66D',
        },
        brand: {
          50: '#f0fdf4',
          500: '#55E6A5',
          600: '#35D993',
          700: '#22b575',
          900: '#101914',
        }
      },
      borderRadius: {
        'obsidian-sm': '8px',
        'obsidian': '10px',
        'obsidian-lg': '12px',
      },
      boxShadow: {
        'glow-amber': '0 0 24px -2px rgba(255, 198, 109, 0.35)',
        'glow-jade': '0 0 24px -2px rgba(85, 230, 165, 0.35)',
        'active-step': '0 0 0 4px rgba(255, 198, 109, 0.2), 0 0 16px rgba(255, 198, 109, 0.4)',
        'card-subtle': '0 2px 8px 0 rgba(0, 0, 0, 0.4)',
      }
    },
  },
  plugins: [],
}
