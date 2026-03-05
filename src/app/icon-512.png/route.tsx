import { ImageResponse } from "next/og";

export const runtime = "edge";

export async function GET() {
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
          borderRadius: "100px",
        }}
      >
        <span
          style={{
            fontSize: "280px",
            fontWeight: 800,
            color: "#d4a843",
            lineHeight: 1,
          }}
        >
          M
        </span>
        <span
          style={{
            fontSize: "52px",
            fontWeight: 600,
            color: "#a09488",
            marginTop: "-8px",
            letterSpacing: "6px",
          }}
        >
          AI
        </span>
      </div>
    ),
    { width: 512, height: 512 }
  );
}
