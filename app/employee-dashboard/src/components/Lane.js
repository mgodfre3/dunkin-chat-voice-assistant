var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import clsx from "clsx";
var STATUS_LABELS = {
    arrived: "Arrived",
    ordering: "Ordering",
    paying: "Paying",
    pickup: "Pickup",
    complete: "Complete"
};
var COLOR_CLASS = {
    green: "bg-emerald-100 text-emerald-800",
    yellow: "bg-amber-100 text-amber-900",
    red: "bg-rose-100 text-rose-900"
};
export function Lane(_a) {
    var cars = _a.cars, selectedCarId = _a.selectedCarId, onSelect = _a.onSelect;
    var ordered = __spreadArray([], cars, true).sort(function (a, b) { return a.waitSeconds - b.waitSeconds; });
    return (_jsxs("div", { className: "flex flex-col gap-3", children: [ordered.map(function (car) {
                var _a, _b, _c, _d, _e, _f;
                return (_jsxs("button", { className: clsx("flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left transition hover:border-dunkin-orange/70", selectedCarId === car.carId && "border-dunkin-orange bg-white/10"), onClick: function () { return onSelect(car); }, children: [_jsxs("div", { children: [_jsx("p", { className: "text-xs uppercase tracking-widest text-white/60", children: (_a = STATUS_LABELS[car.status]) !== null && _a !== void 0 ? _a : car.status }), _jsx("p", { className: "text-lg font-semibold text-white", children: (_c = (_b = car.crmSummary) === null || _b === void 0 ? void 0 : _b.name) !== null && _c !== void 0 ? _c : car.carId }), _jsx("p", { className: "text-sm text-white/70", children: (_e = (_d = car.crmSummary) === null || _d === void 0 ? void 0 : _d.rewardsStatus) !== null && _e !== void 0 ? _e : "Unknown tier" })] }), _jsxs("div", { className: "text-right", children: [_jsxs("span", { className: clsx("rounded-full px-3 py-1 text-xs font-semibold", (_f = COLOR_CLASS[car.waitColor]) !== null && _f !== void 0 ? _f : COLOR_CLASS.green), children: [car.waitSeconds, "s"] }), _jsx("p", { className: "text-xs text-white/60", children: "Wait" })] })] }, car.carId));
            }), !ordered.length && _jsx("p", { className: "text-sm text-white/60", children: "No cars in queue." })] }));
}
