import { DriveThruCarState } from "@/hooks/useDashboardSocket";
type LaneProps = {
    cars: DriveThruCarState[];
    selectedCarId?: string;
    onSelect: (car: DriveThruCarState) => void;
};
export declare function Lane({ cars, selectedCarId, onSelect }: LaneProps): import("react/jsx-runtime").JSX.Element;
export {};
