export type DemoDevice = {
    mac: string;
    label: string;
    customerName: string;
    rewardsStatus: string;
};

export const demoDevices: DemoDevice[] = [
    {
        mac: "B4-8C-9D-11-22-33",
        label: "Sarah's Jeep Compass",
        customerName: "Sarah Kim",
        rewardsStatus: "Gold"
    },
    {
        mac: "88-5F-66-41-2C-90",
        label: "Jamal's F150",
        customerName: "Jamal Roberts",
        rewardsStatus: "Platinum"
    },
    {
        mac: "A0-BC-D4-55-19-EE",
        label: "Lena's Mini Cooper",
        customerName: "Lena Ortiz",
        rewardsStatus: "Silver"
    },
    {
        mac: "5C-77-E6-0D-47-AB",
        label: "Devon's Model Y",
        customerName: "Devon Lee",
        rewardsStatus: "Bronze"
    }
];
