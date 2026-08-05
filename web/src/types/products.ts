export type CategorySummary = { name: string; count: number };
export type CategoryDetail = { main: string; sub: string; count: number; uniqueItems: number };
export type ReviewItem = { itemName: string; orderCount: number; lastOrderDate: string };

export type ProductDashboardData = {
  total: number;
  uniqueItems: number;
  classified: number;
  reviewCount: number;
  updatedAt: string;
  categories: CategorySummary[];
  categoryDetails: CategoryDetail[];
  reviewItems: ReviewItem[];
  productAnalytics: { name: string; orders: number; quantity: number; rate: number; previousOrders: number; change: number | null; items: string[] }[];
  aiReport: string[];
};
