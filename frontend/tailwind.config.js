/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Base light-theme surfaces (Section 44.1)
        canvas: "#FAFAFA",
        surface: "#FFFFFF",
        "surface-muted": "#F4F5F7",
        border: {
          DEFAULT: "#E5E7EB",
          subtle: "#EEF0F2",
        },
        ink: {
          DEFAULT: "#111827",
          muted: "#6B7280",
          faint: "#9CA3AF",
        },
        // Brand / accent
        brand: {
          50: "#EEF2FF",
          100: "#E0E7FF",
          200: "#C7D2FE",
          300: "#A5B4FC",
          400: "#818CF8",
          500: "#6366F1",
          600: "#4F46E5",
          700: "#4338CA",
          800: "#3730A3",
        },
        // Semantic status colors (Section 44.1 / 45)
        healthy: { bg: "#ECFDF5", border: "#A7F3D0", text: "#047857", dot: "#10B981" },
        warning: { bg: "#FFFBEB", border: "#FDE68A", text: "#B45309", dot: "#F59E0B" },
        critical: { bg: "#FEF2F2", border: "#FECACA", text: "#B91C1C", dot: "#EF4444" },
        info: { bg: "#EFF6FF", border: "#BFDBFE", text: "#1D4ED8", dot: "#3B82F6" },
        neutral: { bg: "#F3F4F6", border: "#E5E7EB", text: "#4B5563", dot: "#9CA3AF" },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(16, 24, 40, 0.04), 0 1px 3px 0 rgba(16, 24, 40, 0.06)",
        "card-hover": "0 4px 8px -2px rgba(16, 24, 40, 0.08), 0 2px 4px -2px rgba(16, 24, 40, 0.06)",
        popover: "0 12px 24px -6px rgba(16, 24, 40, 0.12), 0 4px 8px -4px rgba(16, 24, 40, 0.08)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
      keyframes: {
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "pulse-soft": "pulse-soft 1.8s ease-in-out infinite",
        "fade-in": "fade-in 0.25s ease-out",
      },
    },
  },
  plugins: [],
};
