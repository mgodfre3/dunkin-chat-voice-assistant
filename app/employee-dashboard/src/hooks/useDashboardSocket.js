var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
import { useEffect, useMemo, useState } from "react";
export default function useDashboardSocket() {
    var _a = useState([]), cars = _a[0], setCars = _a[1];
    var _b = useState(null), metrics = _b[0], setMetrics = _b[1];
    var _c = useState([]), orders = _c[0], setOrders = _c[1];
    var _d = useState(false), connected = _d[0], setConnected = _d[1];
    useEffect(function () {
        var protocol = window.location.protocol === "https:" ? "wss" : "ws";
        var ws = new WebSocket("".concat(protocol, "://").concat(window.location.host, "/dashboard"));
        ws.onopen = function () { return setConnected(true); };
        ws.onclose = function () { return setConnected(false); };
        ws.onmessage = function (event) {
            var data = JSON.parse(event.data);
            switch (data.type) {
                case "dashboard.snapshot":
                case "lane.snapshot":
                case "session.assigned":
                case "car.arrived":
                case "car.crm_updated":
                case "car.complete":
                case "lane.reset":
                    if (data.cars) {
                        setCars(data.cars);
                    }
                    if (data.metrics) {
                        setMetrics(data.metrics);
                    }
                    break;
                case "dashboard.order_update":
                    setOrders(function (prev) {
                        var _a, _b;
                        var next = __spreadArray([
                            {
                                carId: data.carId,
                                sessionId: data.sessionId,
                                orderSummary: (_a = data.orderSummary) !== null && _a !== void 0 ? _a : {},
                                timestamp: (_b = data.timestamp) !== null && _b !== void 0 ? _b : new Date().toISOString()
                            }
                        ], prev, true);
                        return next.slice(0, 12);
                    });
                    break;
            }
        };
        return function () {
            ws.close();
        };
    }, []);
    var activeCars = useMemo(function () { return cars.filter(function (car) { return car.status !== "complete"; }); }, [cars]);
    return {
        cars: activeCars,
        metrics: metrics,
        orders: orders,
        connected: connected
    };
}
