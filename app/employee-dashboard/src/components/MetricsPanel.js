import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
var metricCards = function (metrics) {
    if (!metrics) {
        return [
            { label: "Cars in queue", value: "--", accent: "text-white" },
            { label: "Avg wait", value: "--", accent: "text-white" },
            { label: "Orders/hr", value: "--", accent: "text-white" },
            { label: "Recognized", value: "--", accent: "text-white" }
        ];
    }
    return [
        { label: "Cars in queue", value: metrics.carsInQueue.toString(), accent: "text-dunkin-orange" },
        { label: "Avg wait", value: "".concat(metrics.avgWaitSeconds, "s"), accent: "text-dunkin-pink" },
        { label: "Orders/hr", value: metrics.ordersPerHour.toString(), accent: "text-emerald-400" },
        { label: "Recognized", value: "".concat(metrics.recognizedPercent, "%"), accent: "text-amber-300", sublabel: "CRM hits" }
    ];
};
export function MetricsPanel(_a) {
    var metrics = _a.metrics;
    return (_jsx("div", { className: "grid grid-cols-2 gap-3 lg:grid-cols-4", children: metricCards(metrics).map(function (card) { return (_jsxs("div", { className: "rounded-2xl border border-white/10 bg-white/5 p-4", children: [_jsx("p", { className: "text-xs uppercase tracking-widest text-white/60", children: card.label }), _jsx("p", { className: "text-2xl font-semibold ".concat(card.accent), children: card.value }), card.sublabel && _jsx("p", { className: "text-xs text-white/60", children: card.sublabel })] }, card.label)); }) }));
}
