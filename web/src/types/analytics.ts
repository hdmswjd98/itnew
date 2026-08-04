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
  industries: { group: string; name: string; customers: number; orders: number; quantity: number }[];
  topProducts: { group: string; itemName: string; orders: number; quantity: number }[];
  validation: { item: string; status: string; detail: string }[];
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
};
