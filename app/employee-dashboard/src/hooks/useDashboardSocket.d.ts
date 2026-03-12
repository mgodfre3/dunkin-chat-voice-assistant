export type DriveThruCarState = {
    carId: string;
    status: string;
    macAddress?: string | null;
    sessionId?: string | null;
    crmCustomerId?: string | null;
    crmSummary?: Record<string, unknown> | null;
    orderTotal?: number | null;
    waitSeconds: number;
    waitColor: string;
};
export type DashboardMetrics = {
    carsInQueue: number;
    avgWaitSeconds: number;
    ordersPerHour: number;
    recognizedPercent: number;
    timestamp?: string;
};
export type OrderEvent = {
    carId: string;
    sessionId: string;
    orderSummary: Record<string, unknown>;
    timestamp: string;
};
export default function useDashboardSocket(): {
    cars: DriveThruCarState[];
    metrics: DashboardMetrics | null;
    orders: OrderEvent[];
    connected: boolean;
};
