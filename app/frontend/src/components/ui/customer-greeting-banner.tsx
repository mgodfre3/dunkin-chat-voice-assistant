import { X } from "lucide-react";
import { CustomerGreetingPayload } from "@/types";

interface Props {
    greeting: CustomerGreetingPayload;
    onClear: () => void;
}

const formatOrderLine = (item: { item: string; size?: string | null; quantity: number }) => {
    const size = item.size ? `${item.size} ` : "";
    const qty = item.quantity > 1 ? `${item.quantity} x ` : "";
    return `${qty}${size}${item.item}`.trim();
};

export default function CustomerGreetingBanner({ greeting, onClear }: Props) {
    const progress = Math.min(100, Math.round((greeting.loyaltyScore / Math.max(greeting.loyaltyGoal, 1)) * 100));
    const usual = greeting.usualOrder?.length ? greeting.usualOrder.map(formatOrderLine).join(", ") : "their usual favorites";

    return (
        <div className="rounded-2xl border border-[#FF671F]/30 bg-gradient-to-r from-[#FFEBD2] via-white to-[#FFF6EF] p-4 shadow-sm">
            <div className="flex items-start gap-3">
                <div className="flex-1 space-y-1">
                    <p className="text-xs font-semibold uppercase tracking-wide text-[#E3007F]">Recognized Guest</p>
                    <h3 className="text-lg font-semibold text-[#7A2E10]">
                        Welcome back, {greeting.name}! Want your usual?
                    </h3>
                    <p className="text-sm text-[#5b220b]">
                        {usual}
                    </p>
                    {greeting.suggestedSales?.length > 0 && (
                        <p className="text-xs uppercase tracking-wide text-[#E3007F]">
                            Crew hint: {greeting.suggestedSales[0]}
                        </p>
                    )}
                </div>
                <button
                    className="rounded-full bg-white/70 p-1 text-[#C14200] transition hover:bg-white"
                    aria-label="Dismiss greeting"
                    onClick={onClear}
                >
                    <X className="h-4 w-4" />
                </button>
            </div>
            <div className="mt-3 flex flex-col gap-2 md:flex-row md:items-center">
                <div className="flex-1">
                    <div className="flex items-center justify-between text-xs font-semibold text-[#C14200]">
                        <span>{greeting.rewardsStatus} Rewards</span>
                        <span>
                            {greeting.loyaltyScore}/{greeting.loyaltyGoal}
                        </span>
                    </div>
                    <div className="mt-1 h-2 rounded-full bg-white/60">
                        <div className="h-2 rounded-full bg-[#FF671F]" style={{ width: `${progress}%` }} />
                    </div>
                </div>
                {greeting.curbsidePreferred && (
                    <span className="rounded-full border border-[#FF671F]/40 bg-white/80 px-3 py-1 text-xs font-semibold text-[#C14200]">
                        Prefers curbside handoff
                    </span>
                )}
            </div>
        </div>
    );
}
