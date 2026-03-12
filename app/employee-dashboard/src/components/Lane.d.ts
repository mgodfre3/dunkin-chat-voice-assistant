import { DriveThruCarState } from "@/hooks/useDashboardSocket";
type LaneProps = {
    cars: DriveThruCarState[];
    selectedCarId?: string;
    onSelect: (car: DriveThruCarState) => void;
    onComplete: (carId: string) => void;
};
export declare function Lane({ cars, selectedCarId, onSelect, onComplete }: LaneProps): import("react/jsx-runtime").JSX.Element;
export {};
