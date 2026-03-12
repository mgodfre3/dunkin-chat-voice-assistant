import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import dayjs from "dayjs";
export function OrderFeed(_a) {
    var orders = _a.orders;
    return (_jsxs("div", { className: "rounded-3xl border border-white/5 bg-white/5 p-5 text-white", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsx("h3", { className: "text-lg font-semibold", children: "Live Orders" }), _jsxs("span", { className: "text-xs text-white/60", children: [orders.length, " events"] })] }), _jsxs("div", { className: "mt-4 space-y-3 text-sm", children: [orders.length === 0 && _jsx("p", { className: "text-white/60", children: "No orders yet." }), orders.map(function (order) {
                        var _a, _b, _c, _d, _e;
                        return (_jsxs("div", { className: "rounded-2xl border border-white/10 bg-white/5 p-3", children: [_jsx("p", { className: "text-xs uppercase tracking-widest text-white/50", children: dayjs(order.timestamp).format("h:mm:ss A") }), _jsxs("p", { className: "text-base font-semibold", children: [(_c = (_b = (_a = order.orderSummary) === null || _a === void 0 ? void 0 : _a.items) === null || _b === void 0 ? void 0 : _b.length) !== null && _c !== void 0 ? _c : 0, " items \u2022 $", String((_e = (_d = order.orderSummary) === null || _d === void 0 ? void 0 : _d.finalTotal) !== null && _e !== void 0 ? _e : "--")] }), _jsxs("p", { className: "text-xs text-white/60", children: ["Car ", order.carId] })] }, order.timestamp + order.sessionId));
                    })] })] }));
}
