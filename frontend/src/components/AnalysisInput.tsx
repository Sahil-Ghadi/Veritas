import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Link2, Type, Image as ImageIcon, Sparkles, Loader2, X, Upload } from "lucide-react";
import { cn } from "@/lib/utils";

type InputMode = "url" | "text" | "image";

interface AnalysisInputProps {
  onAnalyze: (mode: InputMode, value: string) => void;
  loading?: boolean;
}

export const AnalysisInput = ({ onAnalyze, loading }: AnalysisInputProps) => {
  const [mode, setMode] = useState<InputMode>("url");
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [image, setImage] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const tabs: { id: InputMode; label: string; icon: typeof Link2 }[] = [
    { id: "url", label: "URL", icon: Link2 },
    { id: "text", label: "Text", icon: Type },
    { id: "image", label: "Image", icon: ImageIcon },
  ];

  const handleSubmit = () => {
    const value = mode === "url" ? url : mode === "text" ? text : image || "";
    if (!value.trim()) return;
    onAnalyze(mode, value);
  };

  const handleFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => setImage(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  return (
    <div className="relative">
      {/* Glow */}
      <div className="absolute -inset-4 bg-gradient-mesh opacity-20 blur-3xl rounded-full pointer-events-none" />

      <div className="relative bg-gradient-card border border-border/60 rounded-2xl p-2 shadow-elegant">
        {/* Tabs */}
        <div className="flex items-center gap-1 p-1 bg-secondary/40 rounded-xl mb-2">
          {tabs.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => setMode(t.id)}
                className={cn(
                  "flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-300 ease-smooth",
                  mode === t.id
                    ? "bg-background text-foreground shadow-card"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Input area */}
        <div className="p-4">
          {mode === "url" && (
            <div className="space-y-3 animate-fade-in">
              <Input
                type="url"
                placeholder="https://example.com/news-article"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="h-12 text-base bg-background/50 border-border/60"
              />
              <p className="text-xs text-muted-foreground">Paste any news article URL — we'll extract and verify the claims.</p>
            </div>
          )}

          {mode === "text" && (
            <div className="space-y-3 animate-fade-in">
              <Textarea
                placeholder="Paste the news content you want to verify..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="min-h-[140px] text-base bg-background/50 border-border/60 resize-none"
              />
              <p className="text-xs text-muted-foreground">{text.length} characters · works best with full articles</p>
            </div>
          )}

          {mode === "image" && (
            <div className="space-y-3 animate-fade-in">
              {image ? (
                <div className="relative rounded-xl overflow-hidden border border-border/60 bg-background/50">
                  <img src={image} alt="Upload preview" className="w-full max-h-72 object-contain" />
                  <button
                    onClick={() => setImage(null)}
                    className="absolute top-2 right-2 p-1.5 rounded-full bg-background/80 hover:bg-background"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => fileRef.current?.click()}
                  className="w-full h-40 border-2 border-dashed border-border/60 rounded-xl flex flex-col items-center justify-center gap-2 hover:border-primary/50 hover:bg-primary/5 transition-all duration-300 group"
                >
                  <Upload className="h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
                  <p className="text-sm font-medium">Drop an image or click to upload</p>
                  <p className="text-xs text-muted-foreground">Screenshots, headlines, social posts</p>
                </button>
              )}
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
            </div>
          )}

          <Button
            onClick={handleSubmit}
            disabled={loading}
            size="lg"
            className="w-full mt-4 bg-gradient-primary text-primary-foreground hover:opacity-90 shadow-glow font-semibold transition-all duration-300 ease-smooth hover:scale-[1.01]"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" /> Analyze for Truth
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
