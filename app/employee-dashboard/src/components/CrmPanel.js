import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
function SectionTitle(_a) {
    var title = _a.title;
    return _jsx("p", { className: "text-xs uppercase tracking-[0.3em] text-white/50", children: title });
}
export function CrmPanel(_a) {
    var _b, _c, _d;
    var car = _a.car;
    if (!car || !car.crmSummary) {
        return (_jsx("div", { className: "rounded-3xl border border-white/5 bg-white/5 p-5 text-white/70", children: _jsx("p", { className: "font-semibold", children: "Select a car to view CRM insights" }) }));
    }
    var summary = car.crmSummary;
    var usual = ((_b = summary.usualOrder) === null || _b === void 0 ? void 0 : _b.map(renderItem).join(" · ")) || "No saved order";
    var favorites = ((_c = summary.favoriteItems) === null || _c === void 0 ? void 0 : _c.map(renderItem).join(" · ")) || "--";
    return (_jsxs("div", { className: "rounded-3xl border border-white/5 bg-white/5 p-5 text-white", children: [_jsxs("div", { className: "flex items-start justify-between", children: [_jsxs("div", { children: [_jsxs("p", { className: "text-sm text-white/60", children: [summary.rewardsStatus, " Rewards"] }), _jsx("h2", { className: "text-2xl font-semibold", children: summary.name })] }), _jsxs("div", { className: "text-right", children: [_jsx("p", { className: "text-xs uppercase tracking-[0.3em] text-white/40", children: "Loyalty" }), _jsxs("p", { className: "text-lg font-semibold text-dunkin-orange", children: [summary.loyaltyScore, "/", summary.loyaltyGoal] })] })] }), _jsxs("div", { className: "mt-4 space-y-3 text-sm", children: [_jsxs("div", { children: [_jsx(SectionTitle, { title: "Usual" }), _jsx("p", { children: usual })] }), _jsxs("div", { children: [_jsx(SectionTitle, { title: "Favorites" }), _jsx("p", { children: favorites })] }), ((_d = summary.suggestedSales) === null || _d === void 0 ? void 0 : _d.length) ? (_jsxs("div", { children: [_jsx(SectionTitle, { title: "Crew hints" }), _jsx("ul", { className: "list-disc pl-4 text-white/80", children: summary.suggestedSales.slice(0, 2).map(function (hint) { return (_jsx("li", { children: hint }, hint)); }) })] })) : null] })] }));
}
function renderItem(item) {
    if (!item)
        return "";
    var size = item.size ? "".concat(item.size, " ") : "";
    var qty = item.quantity && item.quantity > 1 ? "".concat(item.quantity, "x ") : "";
    return "".concat(qty).concat(size).concat(item.item).trim();
}
