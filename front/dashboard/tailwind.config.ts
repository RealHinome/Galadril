import type { Config } from "tailwindcss";

export default <Partial<Config>>{
  theme: {
    extend: {
      colors: {
        galadril: {
          DEFAULT: "#f59e0b",
          hover: "#d97706",
        },
      },
    },
  },
};
