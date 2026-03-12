import clsx from "clsx";
import { DriveThruCarState } from "@/hooks/useDashboardSocket";

const STATUS_LABELS: Record<string, string> = {
  arrived: "Arrived",
  ordering: "Ordering",
  paying: "Paying",
  pickup: "Pickup",
  complete: "Complete"
};

const COLOR_CLASS: Record<string, string> = {
  green: "bg-emerald-100 text-emerald-800",
  yellow: "bg-amber-100 text-amber-900",
  red: "bg-rose-100 text-rose-900"
};

type LaneProps = {
  cars: DriveThruCarState[];
  selectedCarId?: string;
  onSelect: (car: DriveThruCarState) => void;
};

export function Lane({ cars, selectedCarId, onSelect }: LaneProps) {
  const ordered = [...cars].sort((a, b) => a.waitSeconds - b.waitSeconds);
  return (
    <div className="flex flex-col gap-3">
      {ordered.map(car => (
        <button
          key={car.carId}
          className={clsx(
            "flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left transition hover:border-dunkin-orange/70",
            selectedCarId === car.carId && "border-dunkin-orange bg-white/10"
          )}
          onClick={() => onSelect(car)}
        >
          <div>
            <p className="text-xs uppercase tracking-widest text-white/60">{STATUS_LABELS[car.status] ?? car.status}</p>
            <p className="text-lg font-semibold text-white">{(car.crmSummary?.name as string) ?? car.carId}</p>
            <p className="text-sm text-white/70">{(car.crmSummary?.rewardsStatus as string) ?? "Unknown tier"}</p>
          </div>
          <div className="text-right">
            <span className={clsx("rounded-full px-3 py-1 text-xs font-semibold", COLOR_CLASS[car.waitColor] ?? COLOR_CLASS.green)}>
              {car.waitSeconds}s
            </span>
            <p className="text-xs text-white/60">Wait</p>
          </div>
        </button>
      ))}
      {!ordered.length && <p className="text-sm text-white/60">No cars in queue.</p>}
    </div>
  );
}
