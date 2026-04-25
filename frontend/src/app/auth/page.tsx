"use client";

import { useState } from "react";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "@/lib/firebase";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LogIn, Shield, ArrowLeft } from "lucide-react";
import Link from "next/link";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function AuthPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      setError("");
      
      const result = await signInWithPopup(auth, googleProvider);
      const idToken = await result.user.getIdToken();
      
      // Send token to backend
      const res = await fetch(`${API_BASE_URL}/auth/google`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token: idToken }),
      });
      
      if (!res.ok) {
        throw new Error("Failed to authenticate with backend");
      }
      
      // Successfully authenticated
      router.push("/analyze");
    } catch (err: any) {
      console.error("Login failed:", err);
      setError(err.message || "An error occurred during sign in.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background relative overflow-hidden">
      {/* Background gradients similar to landing page */}
      <div className="absolute inset-0 bg-gradient-hero pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[80px] pointer-events-none" />

      {/* Back button */}
      <Button 
        variant="ghost" 
        size="sm" 
        asChild 
        className="absolute top-6 left-6 md:top-10 md:left-10 text-muted-foreground hover:text-foreground z-10"
      >
        <Link href="/">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to home
        </Link>
      </Button>

      {/* Auth Card */}
      <div className="w-full max-w-md relative z-10 animate-fade-in-up">
        <div className="absolute -inset-1 bg-gradient-to-r from-primary/30 to-accent/30 rounded-2xl blur-xl opacity-50" />
        <Card className="relative bg-card/60 backdrop-blur-xl border-white/10 shadow-elegant overflow-hidden">
          {/* Top highlight */}
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          
          <CardHeader className="space-y-4 text-center pt-8">
            <div className="mx-auto bg-primary/10 w-16 h-16 rounded-2xl flex items-center justify-center border border-primary/20 mb-2">
              <Shield className="h-8 w-8 text-primary" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-3xl font-display font-medium tracking-tight">
                Welcome to Veritas
              </CardTitle>
              <CardDescription className="text-muted-foreground text-base">
                Sign in to your account to continue
              </CardDescription>
            </div>
          </CardHeader>
          
          <CardContent className="grid gap-6 pb-8 pt-4 px-8">
            {error && (
              <div className="p-3 text-sm text-destructive-foreground bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2 animate-in fade-in slide-in-from-top-1">
                <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-destructive" />
                {error}
              </div>
            )}
            
            <Button 
              size="lg"
              className="w-full font-medium h-12 bg-white text-zinc-900 hover:bg-zinc-100 hover:text-zinc-900 shadow-lg border border-transparent transition-all duration-300 relative overflow-hidden group" 
              onClick={handleGoogleLogin} 
              disabled={loading}
            >
              <div className="absolute inset-0 bg-white/40 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
              <span className="relative flex items-center gap-3">
                {loading ? (
                  <>
                    <span className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-900 border-r-transparent"></span>
                    Authenticating...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path
                        fill="currentColor"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="currentColor"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Continue with Google
                  </>
                )}
              </span>
            </Button>
            
            <p className="text-center text-xs text-muted-foreground mt-4">
              By continuing, you agree to our Terms of Service and Privacy Policy.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
