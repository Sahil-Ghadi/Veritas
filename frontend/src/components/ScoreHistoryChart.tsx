"use client";

import { ScoreHistoryEntry } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { Card } from "./ui/card";
import { format } from "date-fns";

interface ScoreHistoryChartProps {
  data: ScoreHistoryEntry[];
}

export const ScoreHistoryChart = ({ data }: ScoreHistoryChartProps) => {
  if (!data || data.length === 0) return null;

  const chartData = data.map((entry) => ({
    ...entry,
    formattedDate: format(new Date(entry.date), "MMM d, HH:mm"),
    // Just the score for the Y axis
    score: entry.score,
  }));

  return (
    <Card className="p-6 bg-gradient-card border-border/40 shadow-sm overflow-hidden">
      <div className="mb-6">
        <h3 className="font-serif text-lg font-semibold">Credibility Timeline</h3>
        <p className="text-xs text-muted-foreground mt-1">
          How this story's verification score has evolved through community disputes.
        </p>
      </div>

      <div className="h-[240px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.4} />
            <XAxis
              dataKey="formattedDate"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              minTickGap={30}
            />
            <YAxis
              domain={[0, 100]}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload as ScoreHistoryEntry;
                  return (
                    <div className="bg-background border border-border p-3 rounded-lg shadow-elegant animate-in fade-in zoom-in duration-200">
                      <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider mb-1">
                        {format(new Date(data.date), "PPP p")}
                      </p>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg font-bold text-primary">{data.score}%</span>
                        <span className="text-xs text-foreground/80 font-medium">Credibility</span>
                      </div>
                      <p className="text-sm text-foreground/90 border-t border-border/40 pt-2 leading-tight max-w-[200px]">
                        {data.reason}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="score"
              stroke="hsl(var(--primary))"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#colorScore)"
              animationDuration={1500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
