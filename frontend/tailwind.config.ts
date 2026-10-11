export default {
  theme: {
    extend: {
      colors: {
        surface: "var(--surface)",
        raised: "var(--surface-raised)",
        border: "var(--border)",
        text: "var(--text)",
        muted: "var(--text-muted)",
        accent: "var(--accent)",
        allow: {
          DEFAULT: "var(--allow-fg)",
          bg: "var(--allow-bg)",
          border: "var(--allow-border)",
        },
        review: {
          DEFAULT: "var(--review-fg)",
          bg: "var(--review-bg)",
          border: "var(--review-border)",
        },
        block: {
          DEFAULT: "var(--block-fg)",
          bg: "var(--block-bg)",
          border: "var(--block-border)",
        },
        info: {
          DEFAULT: "var(--info-fg)",
          bg: "var(--info-bg)",
          border: "var(--info-border)",
        },
      },
      fontFamily: {
        sans: ["Inter Variable", "sans-serif"],
        mono: ["JetBrains Mono Variable", "monospace"],
      },
      borderRadius: { sm: "6px", md: "10px", lg: "16px" },
      spacing: {
        1: "4px",
        2: "8px",
        3: "12px",
        4: "16px",
        5: "20px",
        6: "24px",
        8: "32px",
        10: "40px",
      },
    },
  },
};
