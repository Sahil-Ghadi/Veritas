"use client";

import Link from "next/link";
import Image from "next/image";
import { SiteFooter } from "@/components/SiteFooter";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { VerdictBadge } from "@/components/VerdictBadge";
import { useEffect, useState } from "react";
import { onAuthStateChanged } from "firebase/auth";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/firebase";
import {
  ArrowRight,
  ScanSearch,
  GitBranch,
  Scale,
  Users,
  Sparkles,
  ShieldCheck,
  Zap,
  Quote,
  Database,
  Eye,
  MessageSquareWarning,
  Shield,
  CheckCircle2,
} from "lucide-react";

const Landing = () => {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (user) => {
      if (user) {
        router.replace("/analyze");
        return;
      }
      setCheckingAuth(false);
    });
    return () => unsub();
  }, [router]);

  if (checkingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-muted-foreground">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* LANDING NAV */}
      <header className="absolute top-0 inset-x-0 z-50 h-20 flex items-center px-6 md:px-10 border-b border-white/5 bg-background/50 backdrop-blur-md">
        <div className="flex-1 flex items-center">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="relative shrink-0">
              <Shield className="h-6 w-6 text-primary transition-transform duration-500 group-hover:scale-110" />
              <div className="absolute inset-0 blur-md bg-primary/40 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            </div>
            <span className="font-serif text-xl font-semibold tracking-tight">Veritas</span>
          </Link>
        </div>

        <div className="flex-1 flex items-center justify-end gap-4">
          <Button variant="ghost" asChild className="hidden sm:flex hover:text-foreground">
            <Link href="/auth">Sign in</Link>
          </Button>
          <Button asChild className="hidden sm:flex bg-primary text-primary-foreground hover:opacity-90 shadow-glow">
            <Link href="/auth">Get Started</Link>
          </Button>
        </div>
      </header>

      <main className="flex-1 min-w-0 flex flex-col">
        {/* HERO */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-hero pointer-events-none" />
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-primary/10 rounded-full blur-3xl pointer-events-none" />

          <div className="container relative pt-20 pb-24 md:pt-32 md:pb-32">
            <div className="max-w-4xl mx-auto text-center">

              <h1 className="font-display text-[clamp(2.25rem,5vw,4.5rem)] font-medium text-balance animate-fade-in-up text-foreground">
                Truth, broken down<br className="hidden sm:block" />
                <span className="sm:hidden"> </span>to its <span className="italic font-normal text-accent">smallest claim.</span>
              </h1>

              <p className="mt-8 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed text-pretty animate-fade-in-up" style={{ animationDelay: "100ms" }}>
                Veritas analyzes news from any URL, text, or image - splitting it into individual claims, hunting supporting and contradictory evidence, and delivering a transparent verdict you can actually trust.
              </p>

              <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3 animate-fade-in-up" style={{ animationDelay: "200ms" }}>
                <Button size="lg" asChild className="bg-gradient-primary text-primary-foreground hover:opacity-90 shadow-glow font-semibold h-12 px-6">
                  <Link href="/auth">
                    Analyze a story <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild className="h-12 px-6">
                  <Link href="/auth">Browse community</Link>
                </Button>
              </div>

              <div className="mt-16 flex items-center justify-center gap-8 text-xs text-muted-foreground font-mono animate-fade-in" style={{ animationDelay: "400ms" }}>
                <div className="flex items-center gap-1.5"><Zap className="h-3 w-3 text-primary" />~12s avg</div>
                <div className="hidden sm:flex items-center gap-1.5"><Database className="h-3 w-3 text-primary" />community-verified</div>
                <div className="flex items-center gap-1.5"><Eye className="h-3 w-3 text-primary" />fully transparent</div>
              </div>
            </div>

            {/* Demo card */}
            <div className="mt-20 max-w-3xl mx-auto animate-fade-in-up" style={{ animationDelay: "500ms" }}>
              <div className="relative">
                <div className="absolute -inset-2 bg-gradient-accent opacity-[0.06] blur-3xl rounded-3xl" />
                <Card className="relative bg-card border-border p-6 md:p-8 shadow-elegant overflow-hidden">
                  <div className="absolute top-0 right-0 w-64 h-64 bg-accent/[0.04] rounded-full blur-3xl" />
                  <div className="relative">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-xs font-mono text-muted-foreground">/ live analysis preview</span>
                      <VerdictBadge verdict="false" size="sm" />
                    </div>
                    <p className="font-serif text-xl md:text-2xl leading-snug mb-6">
                      "Scientists confirm coffee reverses aging in new 2024 study"
                    </p>
                    <div className="space-y-3">
                      {[
                        { label: "Claim 1: Coffee reverses biological aging", verdict: "false" as const, score: 8 },
                        { label: "Claim 2: Harvard researchers led the study", verdict: "false" as const, score: 4 },
                        { label: "Claim 3: Coffee reduces inflammation markers", verdict: "mostly-true" as const, score: 72 },
                      ].map((c, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-3 p-3 rounded-lg bg-secondary/40 border border-border/40 animate-slide-in-right"
                          style={{ animationDelay: `${600 + i * 150}ms` }}
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm truncate">{c.label}</p>
                            <div className="mt-1.5 h-1 bg-secondary rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${c.score < 30 ? "bg-destructive" : c.score < 70 ? "bg-warning" : "bg-success"}`}
                                style={{ width: `${c.score}%`, transition: "width 1.5s ease-out" }}
                              />
                            </div>
                          </div>
                          <VerdictBadge verdict={c.verdict} size="sm" />
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section id="how" className="container py-24 md:py-32">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <p className="text-xs font-mono uppercase tracking-widest text-accent mb-3">— The pipeline</p>
            <h2 className="font-display text-5xl md:text-6xl font-medium text-balance">
              Every story, dissected<br />
              <span className="italic font-light">with the same rigor.</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: ScanSearch, title: "1. Ingest", body: "URL, raw text, or screenshot. We extract the underlying article." },
              { icon: GitBranch, title: "2. Decompose", body: "AI splits the story into individual factual claims." },
              { icon: Scale, title: "3. Cross-check", body: "Each claim is verified against supporting and contradictory sources." },
              { icon: Sparkles, title: "4. Verdict", body: "A combined credibility score, confidence, and transparent reasoning." },
            ].map((step, i) => (
              <Card key={i} className="bg-gradient-card border-border/60 p-6 hover:border-primary/40 transition-all duration-500 ease-smooth hover:-translate-y-1 group animate-fade-in-up" style={{ animationDelay: `${i * 80}ms` }}>
                <div className="h-10 w-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                  <step.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="font-serif text-xl font-semibold mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{step.body}</p>
              </Card>
            ))}
          </div>
        </section>

        {/* FEATURES */}
        <section className="container py-20">
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: ShieldCheck, title: "Transparent reasoning", body: "Every verdict comes with the evidence trail. No black boxes." },
              { icon: Users, title: "Community-verified", body: "Already analyzed? See what others found instantly. Cached forever." },
              { icon: MessageSquareWarning, title: "Open to dispute", body: "Disagree? Submit a counter-claim and re-run the pipeline." },
            ].map((f, i) => (
              <Card key={i} className="p-6 bg-gradient-card border-border/60 hover:shadow-glow transition-shadow duration-500">
                <f.icon className="h-6 w-6 text-primary mb-4" />
                <h3 className="font-serif text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground">{f.body}</p>
              </Card>
            ))}
          </div>
        </section>

        {/* QUOTE */}
        <section className="container py-24">
          <div className="max-w-3xl mx-auto text-center">
            <Quote className="h-10 w-10 text-accent/40 mx-auto mb-6" />
            <p className="font-display text-3xl md:text-5xl leading-[1.05] text-balance italic font-light text-foreground">
              "In an age of synthetic media, the only defense is{" "}
              <span className="not-italic font-medium text-accent">verifiable transparency.</span>"
            </p>
          </div>
        </section>

        {/* WHATSAPP INTEGRATION */}
        <section className="container py-24 bg-secondary/20 rounded-3xl mb-20 overflow-hidden relative">
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />
          
          <div className="flex flex-col lg:flex-row items-center gap-12 relative z-10">
            <div className="flex-1 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-success/10 text-success text-xs font-mono mb-4">
                <Zap className="h-3 w-3" /> Live on WhatsApp
              </div>
              <h2 className="font-display text-4xl md:text-5xl font-medium mb-6 text-balance">
                Verify news without<br />
                <span className="italic font-light">leaving the chat.</span>
              </h2>
              <p className="text-lg text-muted-foreground mb-8 max-w-xl leading-relaxed">
                Forward any suspicious link or text to the Veritas WhatsApp bot. We'll run it through our pipeline and send you the full verdict in seconds.
              </p>
              
              <div className="space-y-4">
                {[
                  "1. Add +1 (415) 523-8886 to contacts",
                  "2. Send message: 'join path-short'",
                  "3. Forward any article to get a verdict",
                ].map((step, i) => (
                  <div key={i} className="flex items-center gap-3 text-sm font-medium">
                    <CheckCircle2 className="h-4 w-4 text-success" />
                    {step}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex-1 flex justify-center">
              <div className="relative group">
                <div className="absolute -inset-4 bg-gradient-to-r from-success/20 to-primary/20 rounded-2xl blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <Card className="relative p-8 bg-card border-border/60 shadow-elegant flex flex-col items-center">
                  <div className="bg-white p-4 rounded-xl mb-6 shadow-inner overflow-hidden">
                    <Image 
                      src="/Veritas.png" 
                      alt="WhatsApp QR Code" 
                      width={192} 
                      height={192} 
                      className="rounded-lg object-cover"
                    />
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-mono font-bold text-foreground mb-1">SCAN TO START</p>
                    <p className="text-xs text-muted-foreground">Open WhatsApp and scan</p>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="container py-20">
          <Card className="relative overflow-hidden bg-primary border-transparent p-10 md:p-16 text-center text-primary-foreground">
            <div className="absolute inset-0 opacity-30" style={{ background: "radial-gradient(circle at 30% 20%, hsl(14 78% 52% / 0.4), transparent 50%)" }} />
            <div className="relative">
              <h2 className="font-display text-4xl md:text-6xl font-medium mb-4 text-balance text-primary-foreground">
                Stop guessing.<br />
                <span className="italic font-light opacity-80">Start verifying.</span>
              </h2>
              <p className="text-primary-foreground/70 mb-8 max-w-xl mx-auto text-lg">
                The next news article you read deserves a credibility score. Try Veritas free.
              </p>
              <Button size="lg" asChild className="bg-accent text-accent-foreground hover:bg-accent/90 shadow-accent-glow font-medium h-12 px-8">
                <Link href="/analyze">
                  Analyze your first story <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </Card>
        </section>

        <SiteFooter />
      </main>
    </div>
  );
};

export default Landing;
