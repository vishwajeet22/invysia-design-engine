import { Geist, Geist_Mono } from "next/font/google";
import CosmicBackground from "@/components/CosmicBackground";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Invysia Design Engine",
  description: "Advanced AI Design Engine",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased h-screen text-white flex flex-col overflow-hidden font-sans`}
      >
        <CosmicBackground />
        <header className="w-full py-4 px-8 border-b border-white/10 bg-white/5 backdrop-blur-md sticky top-0 z-50 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_rgba(34,211,238,0.8)]"></div>
            <h1 className="text-xl font-bold tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-400 drop-shadow-sm">
              INVYSIA DESIGN ENGINE
            </h1>
          </div>
          <div className="text-xs text-white/50 font-mono tracking-widest uppercase">
            System v2.0
          </div>
        </header>
        <main className="flex-1 relative flex flex-col overflow-hidden w-full h-full">
          {children}
        </main>
      </body>
    </html>
  );
}
