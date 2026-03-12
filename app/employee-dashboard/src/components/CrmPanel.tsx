import { DriveThruCarState } from "@/hooks/useDashboardSocket";

function SectionTitle({ title }: { title: string }) {
  return <p className="text-xs uppercase tracking-[0.3em] text-white/50">{title}</p>;
}

export function CrmPanel({ car }: { car: DriveThruCarState | null }) {
  if (!car || !car.crmSummary) {
    return (
      <div className="rounded-3xl border border-white/5 bg-white/5 p-5 text-white/70">
        <p className="font-semibold">Select a car to view CRM insights</p>
      </div>
    );
  }

  const summary = car.crmSummary as Record<string, any>;
  const usual = (summary.usualOrder as any[])?.map(renderItem).join(" · ") || "No saved order";
  const favorites = (summary.favoriteItems as any[])?.map(renderItem).join(" · ") || "--";

  return (
    <div className="rounded-3xl border border-white/5 bg-white/5 p-5 text-white">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-white/60">{summary.rewardsStatus} Rewards</p>
          <h2 className="text-2xl font-semibold">{summary.name}</h2>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-[0.3em] text-white/40">Loyalty</p>
          <p className="text-lg font-semibold text-dunkin-orange">
            {summary.loyaltyScore}/{summary.loyaltyGoal}
          </p>
        </div>
      </div>
      <div className="mt-4 space-y-3 text-sm">
        <div>
          <SectionTitle title="Usual" />
          <p>{usual}</p>
        </div>
        <div>
          <SectionTitle title="Favorites" />
          <p>{favorites}</p>
        </div>
        {summary.suggestedSales?.length ? (
          <div>
            <SectionTitle title="Crew hints" />
            <ul className="list-disc pl-4 text-white/80">
              {summary.suggestedSales.slice(0, 2).map((hint: string) => (
                <li key={hint}>{hint}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function renderItem(item: any) {
  if (!item) return "";
  const size = item.size ? `${item.size} ` : "";
  const qty = item.quantity && item.quantity > 1 ? `${item.quantity}x ` : "";
  return `${qty}${size}${item.item}`.trim();
}
