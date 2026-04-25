"use client";

import { Shield } from "lucide-react";
import Link from "next/link";

export const SiteFooter = () => {
  return (
    <footer className="border-t border-border/40 mt-20">
      <div className="container py-12 grid gap-8 md:grid-cols-4">
        <div className="space-y-3">
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <span className="font-serif text-lg font-semibold">Veritas</span>
          </Link>
          <p className="text-sm text-muted-foreground max-w-xs">
            Transparent, AI-powered fact-checking for the open web.
          </p>
        </div>
        <div>
          <h4 className="text-sm font-semibold mb-3">Product</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li><Link href="/analyze" className="hover:text-foreground">Analyze</Link></li>
            <li><Link href="/community" className="hover:text-foreground">Community</Link></li>
            <li><a href="#how" className="hover:text-foreground">How it works</a></li>
          </ul>
        </div>
        <div>
          <h4 className="text-sm font-semibold mb-3">Resources</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li><a href="#" className="hover:text-foreground">Methodology</a></li>
            <li><a href="#" className="hover:text-foreground">API</a></li>
            <li><a href="#" className="hover:text-foreground">Sources</a></li>
          </ul>
        </div>
        <div>
          <h4 className="text-sm font-semibold mb-3">Company</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li><a href="#" className="hover:text-foreground">About</a></li>
            <li><a href="#" className="hover:text-foreground">Privacy</a></li>
            <li><a href="#" className="hover:text-foreground">Contact</a></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-border/40">
        <div className="container py-6 flex flex-col md:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <p>© {new Date().getFullYear()} Veritas. All rights reserved.</p>
          <p className="font-mono">Built for truth.</p>
        </div>
      </div>
    </footer>
  );
};
