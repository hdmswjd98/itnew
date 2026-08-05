export type NamedCount = { name: string; count: number };
export type CustomerData = {
  totalCustomers: number;
  groupSummary: NamedCount[];
  churnSummary: NamedCount[];
  eligibleCustomers: number;
  riskCustomers: number;
  returningCustomers: number;
  customers: Record<string, string>[];
  regions: { group: string; name: string; customers: number; rate: number }[];
  pickupRegions: { group: string; name: string; orders: number }[];
  deliveryRegions: { group: string; name: string; orders: number }[];
  pickupGrids: { group: string; lon: number; lat: number; orders: number }[];
  deliveryGrids: { group: string; lon: number; lat: number; orders: number }[];
  channels: { group: string; name: string; orders: number; quantity: number }[];
  industries: { group: string; name: string; customers: number; orders: number; quantity: number }[];
  topProducts: { group: string; itemName: string; orders: number; quantity: number }[];
  validation: { item: string; status: string; detail: string }[];
  categoryOptions: { main: string; sub: string }[];
  today: {
    date: string;
    orders: number;
    previousOrders: number;
    newCustomers: number;
    previousNewCustomers: number;
    hourlyOrders: { hour: string; orders: number }[];
    monthOrders: number;
    monthNewCustomers: number;
    mau: number;
    orderList: { orderId: string; orderTime: string; channel: string; itemName: string; sourceItemName: string; quantity: number; mainCategory: string; subCategory: string }[];
  };
  operations: {
    from: string; to: string; days: number;
    orders: number; previousOrders: number; newCustomers: number; previousNewCustomers: number;
    hourlyOrders: { hour: string; orders: number }[];
    weekdayOrders: { name: string; orders: number }[];
    monthlyOrders: { month: string; orders: number }[];
    orderList: { orderId: string; orderTime: string; channel: string; itemName: string; sourceItemName: string; quantity: number; mainCategory: string; subCategory: string }[];
  };
};

export type MonthlyReport = {
  report_month: string;
  current_sales: number;
  previous_sales: number;
  issues: string[];
  actions: string[];
  results: string[];
  next_month_plan: string;
  partner_requests: string;
  updated_at: string;
};
export type MonthlyData = {
  reports: MonthlyReport[];
  trends: { month: string; orders: number; customers: number; quantity: number }[];
  total_members: number;
};
