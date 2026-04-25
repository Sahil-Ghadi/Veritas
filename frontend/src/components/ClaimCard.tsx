import { Claim } from "@/lib/mockData";
import { Card } from "@/components/ui/card";
import { VerdictBadge } from "./VerdictBadge";
import { CredibilityMeter } from "./CredibilityMeter";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, Quote, Link2, ThumbsUp, ThumbsDown, AlertCircle } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export const ClaimCard = ({ claim, index }: { claim: Claim; index: number }) => {
  const [open, setOpen] = useState(index === 0);

  return (
    <Card
      className="overflow-hidden bg-gradient-card border-border/60 animate-fade-in-up"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <Collapsible open={open} onOpenChange={setOpen}>
        <CollapsibleTrigger className="w-full text-left">
          <div className="p-5 hover:bg-secondary/30 transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-mono text-xs text-muted-foreground">CLAIM #{index + 1}</span>
                  <VerdictBadge verdict={claim.verdict} size="sm" />
                </div>
                <p className="font-serif text-lg leading-snug text-balance">{claim.text}</p>
              </div>
              <ChevronDown
                className={cn(
                  "h-5 w-5 text-muted-foreground transition-transform duration-300 ease-smooth shrink-0 mt-1",
                  open && "rotate-180"
                )}
              />
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <CredibilityMeter score={claim.credibilityScore} label="Credibility" size="sm" />
              <CredibilityMeter score={claim.confidence} label="Confidence" size="sm" />
            </div>
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent className="data-[state=open]:animate-accordion-down data-[state=closed]:animate-accordion-up overflow-hidden">
          <div className="px-5 pb-5 pt-1 space-y-5 border-t border-border/40">
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground flex items-center gap-1.5">
                <Quote className="h-3 w-3" /> Reasoning
              </h4>
              <p className="text-sm text-foreground/90 leading-relaxed">{claim.reasoning}</p>
            </div>

            {claim.supporting.length > 0 && (
              <EvidenceList title="Supporting Evidence" items={claim.supporting} type="support" />
            )}
            {claim.contradicting.length > 0 && (
              <EvidenceList title="Contradicting Evidence" items={claim.contradicting} type="contradict" />
            )}

            {claim.uncertainDetails && claim.uncertainDetails.length > 0 && (
              <div className="rounded-lg bg-warning/5 border border-warning/20 p-3">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-warning flex items-center gap-1.5 mb-2">
                  <AlertCircle className="h-3 w-3" /> Uncertain Details
                </h4>
                <ul className="text-sm space-y-1 text-foreground/80">
                  {claim.uncertainDetails.map((d, i) => (
                    <li key={i} className="flex gap-2"><span className="text-warning">•</span>{d}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

const EvidenceList = ({
  title,
  items,
  type,
}: {
  title: string;
  items: Claim["supporting"];
  type: "support" | "contradict";
}) => {
  const Icon = type === "support" ? ThumbsUp : ThumbsDown;
  const tone = type === "support" ? "text-success" : "text-destructive";
  return (
    <div>
      <h4 className={cn("text-xs font-semibold uppercase tracking-wide flex items-center gap-1.5 mb-2", tone)}>
        <Icon className="h-3 w-3" /> {title}
      </h4>
      <div className="space-y-2">
        {items.map((e) => (
          <a
            key={e.id}
            href={e.url}
            className="block p-3 rounded-lg bg-secondary/40 hover:bg-secondary/70 transition-colors border border-border/40 group"
          >
            <div className="flex items-start justify-between gap-3 mb-1">
              <div className="flex items-center gap-2 min-w-0">
                <Link2 className="h-3 w-3 text-muted-foreground shrink-0" />
                <span className="text-xs font-mono text-muted-foreground truncate">{e.source}</span>
              </div>
              <span className={cn("text-xs font-mono shrink-0", tone)}>{e.credibility}%</span>
            </div>
            <p className="text-sm font-medium group-hover:text-primary transition-colors">{e.title}</p>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">"{e.excerpt}"</p>
          </a>
        ))}
      </div>
    </div>
  );
};
