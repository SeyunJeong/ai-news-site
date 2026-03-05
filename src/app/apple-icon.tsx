import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #1a1520 0%, #121018 100%)",
        }}
      >
        <span
          style={{
            fontSize: "100px",
            fontWeight: 800,
            color: "#d4a843",
            lineHeight: 1,
          }}
        >
          M
        </span>
        <span
          style={{
            fontSize: "18px",
            fontWeight: 600,
            color: "#a09488",
            marginTop: "-4px",
            letterSpacing: "2px",
          }}
        >
          AI
        </span>
      </div>
    ),
    { ...size }
  );
}
