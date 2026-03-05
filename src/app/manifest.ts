import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "MorgenAI — AI 뉴스",
    short_name: "MorgenAI",
    description: "AI 엔지니어를 위한 큐레이션 뉴스",
    start_url: "/",
    display: "standalone",
    background_color: "#121018",
    theme_color: "#121018",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
