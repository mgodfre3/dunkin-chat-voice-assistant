var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
var buttonClass = "rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40";
export function DemoControls() {
    var _this = this;
    var _a = useState(null), running = _a[0], setRunning = _a[1];
    var _b = useState(""), message = _b[0], setMessage = _b[1];
    var _c = useState(null), pending = _c[0], setPending = _c[1];
    useEffect(function () {
        var mounted = true;
        fetch("/simulator/demo")
            .then(function (res) {
            if (!res.ok) {
                throw new Error("status unavailable");
            }
            return res.json();
        })
            .then(function (data) {
            if (mounted) {
                setRunning(Boolean(data.running));
            }
        })
            .catch(function () {
            if (mounted) {
                setRunning(false);
            }
        });
        return function () {
            mounted = false;
        };
    }, []);
    function call(endpoint, options) {
        return __awaiter(this, void 0, void 0, function () {
            var response, payload, error_1, fallback;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        setMessage("");
                        setPending(endpoint);
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 4, 5, 6]);
                        return [4 /*yield*/, fetch(endpoint, __assign({ method: "POST", headers: { "Content-Type": "application/json" } }, options))];
                    case 2:
                        response = _a.sent();
                        if (!response.ok) {
                            throw new Error("Request failed (".concat(response.status, ")"));
                        }
                        return [4 /*yield*/, response.json().catch(function () { return ({}); })];
                    case 3:
                        payload = _a.sent();
                        return [2 /*return*/, payload];
                    case 4:
                        error_1 = _a.sent();
                        fallback = error_1 instanceof Error ? error_1.message : "Unable to update demo";
                        setMessage(fallback);
                        return [2 /*return*/, null];
                    case 5:
                        setPending(null);
                        return [7 /*endfinally*/];
                    case 6: return [2 /*return*/];
                }
            });
        });
    }
    var handleStart = function () { return __awaiter(_this, void 0, void 0, function () {
        var payload;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, call("/simulator/demo/start")];
                case 1:
                    payload = _a.sent();
                    if (payload) {
                        setRunning(true);
                        setMessage("Demo running");
                    }
                    return [2 /*return*/];
            }
        });
    }); };
    var handleStop = function () { return __awaiter(_this, void 0, void 0, function () {
        var payload;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, call("/simulator/demo/stop")];
                case 1:
                    payload = _a.sent();
                    if (payload) {
                        setRunning(false);
                        setMessage("Demo paused");
                    }
                    return [2 /*return*/];
            }
        });
    }); };
    var handleReset = function () { return __awaiter(_this, void 0, void 0, function () {
        var payload;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, call("/simulator/reset")];
                case 1:
                    payload = _a.sent();
                    if (payload) {
                        setMessage("Lane reset");
                    }
                    return [2 /*return*/];
            }
        });
    }); };
    var handleSpawn = function () { return __awaiter(_this, void 0, void 0, function () {
        var payload;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0: return [4 /*yield*/, call("/simulator/spawn")];
                case 1:
                    payload = _a.sent();
                    if (payload) {
                        setMessage("Added demo car");
                    }
                    return [2 /*return*/];
            }
        });
    }); };
    return (_jsxs("section", { className: "rounded-2xl border border-white/10 bg-white/5 p-4", children: [_jsxs("header", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("p", { className: "text-xs uppercase tracking-[0.4em] text-white/40", children: "Demo Controls" }), _jsx("p", { className: "text-lg font-semibold", children: "Drive-Thru Fleet" })] }), _jsx("span", { className: "text-xs font-semibold ".concat(running ? "text-emerald-300" : "text-amber-300"), children: running === null ? "" : running ? "Auto-run enabled" : "Paused" })] }), _jsxs("div", { className: "mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4", children: [_jsx("button", { className: buttonClass, disabled: running || pending === "/simulator/demo/start", onClick: handleStart, children: "Start Demo" }), _jsx("button", { className: buttonClass, disabled: !running || pending === "/simulator/demo/stop", onClick: handleStop, children: "Pause Demo" }), _jsx("button", { className: buttonClass, disabled: pending === "/simulator/reset", onClick: handleReset, children: "Reset Lane" }), _jsx("button", { className: buttonClass, disabled: pending === "/simulator/spawn", onClick: handleSpawn, children: "Add Demo Car" })] }), message && _jsx("p", { className: "mt-3 text-sm text-white/70", children: message })] }));
}
