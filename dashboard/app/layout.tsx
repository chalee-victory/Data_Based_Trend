import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Daejeon Metro Trend Lab",
  description: "대전 도시철도 역별 수송실적 인터랙티브 대시보드",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return <html lang="ko"><body>{children}</body></html>;
}
