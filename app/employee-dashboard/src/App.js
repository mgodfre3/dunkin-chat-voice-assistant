import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import useDashboardSocket from "@/hooks/useDashboardSocket";
import { Lane } from "@/components/Lane";
import { MetricsPanel } from "@/components/MetricsPanel";
import { CrmPanel } from "@/components/CrmPanel";
import { OrderFeed } from "@/components/OrderFeed";
import { DemoControls } from "@/components/DemoControls";
export default function App() {
    var _a = useDashboardSocket(), cars = _a.cars, metrics = _a.metrics, orders = _a.orders, connected = _a.connected;
    var _b = useState(null), selectedCarId = _b[0], setSelectedCarId = _b[1];
    var selectedCar = useMemo(function () {
        var _a, _b;
        if (selectedCarId) {
            return (_a = cars.find(function (car) { return car.carId === selectedCarId; })) !== null && _a !== void 0 ? _a : null;
        }
        return (_b = cars[0]) !== null && _b !== void 0 ? _b : null;
    }, [cars, selectedCarId]);
    return (_jsxs("div", { className: "min-h-screen bg-slate-950 px-6 py-8 text-white", children: [_jsxs("header", { className: "mb-8 flex flex-wrap items-center justify-between gap-4", children: [_jsxs("div", { children: [_jsx("p", { className: "text-xs uppercase tracking-[0.5em] text-white/40", children: "Dunkin Hybrid Edge" }), _jsx("h1", { className: "text-3xl font-semibold", children: "Drive-Thru Command Deck" })] }), _jsx("span", { className: "rounded-full px-4 py-1 text-xs font-semibold ".concat(connected ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/10 text-rose-200"), children: connected ? "Live" : "Disconnected" })] }), _jsxs("div", { className: "space-y-6", children: [_jsx(DemoControls, {}), _jsx(MetricsPanel, { metrics: metrics })] }), _jsxs("div", { className: "mt-6 grid gap-6 lg:grid-cols-[2fr_1fr]", children: [_jsxs("div", { className: "space-y-6", children: [_jsx(Lane, { cars: cars, selectedCarId: selectedCar === null || selectedCar === void 0 ? void 0 : selectedCar.carId, onSelect: function (car) { return setSelectedCarId(car.carId); } }), _jsx(OrderFeed, { orders: orders })] }), _jsx(CrmPanel, { car: selectedCar })] })] }));
}
