const API_URL = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const { headers, ...rest } = options || {};
  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: { "Content-Type": "application/json", ...headers },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export function useToken(): string {
  return localStorage.getItem("admin_token") || "";
}

export interface Course {
  id: string;
  title: string;
  slug: string;
  udemy_url: string;
  description: string;
  instructor: string;
  image_url: string;
  category: string;
  language: string;
  rating: number;
  students_count: number;
  num_reviews: number;
  original_price: number;
  discount_price: number;
  discount_percent: number;
  coupon_code: string;
  affiliate_link: string;
  is_free: boolean;
  status: string;
  detected_at: string;
  manual_link_created_at: string | null;
}

export interface PaginatedCourses {
  items: Course[];
  total: number;
  page: number;
  pages: number;
}

export interface DashboardStats {
  total_courses: number;
  pending_courses: number;
  ready_courses: number;
  published_courses: number;
  total_clicks: number;
  clicks_today: number;
  posts_this_month: number;
}

export interface LogEntry {
  id: string;
  agent_name: string;
  level: string;
  message: string;
  created_at: string;
}

export interface PostSummary {
  id: string;
  slug: string;
  title: string;
  published_at: string;
  course_count: number;
}

export interface PostFull {
  id: string;
  slug: string;
  title: string;
  content_html: string;
  published_at: string;
  courses: Course[];
}

export interface CategoryItem {
  id: string;
  name: string;
  description: string;
  telegram_channels: string[];
  discord_webhooks: string[];
  subreddits: string[];
  twitter_keywords: string[];
  is_active: boolean;
  created_at: string;
}

export interface CategoryCreate {
  name: string;
  description?: string;
  telegram_channels?: string[];
  discord_webhooks?: string[];
  subreddits?: string[];
  twitter_keywords?: string[];
}

export interface PromotionLogItem {
  id: string;
  course_id: string;
  platform: string;
  target: string;
  status: string;
  error_message: string;
  sent_at: string;
}

export interface TelegramChannel {
  username: string;
  title: string;
  members: number;
}

export const api = {
  // Public
  getCourses: (params: Record<string, string>) =>
    request<PaginatedCourses>(`/api/courses?${new URLSearchParams(params)}`),
  getCourse: (slug: string) => request<Course>(`/api/courses/${slug}`),
  getCategories: () => request<{ name: string; count: number }[]>("/api/categories"),
  getStats: () => request<{ total_courses: number; free_courses: number }>("/api/stats"),
  getPosts: () => request<PostSummary[]>("/api/posts"),
  getPost: (slug: string) => request<PostFull>(`/api/posts/${slug}`),
  getRedirectUrl: (id: string) => `${API_URL}/api/courses/${id}/redirect`,

  // Auth
  login: (username: string, password: string) =>
    request<{ access_token: string }>("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  // Admin
  getDashboard: (token: string) =>
    request<DashboardStats>("/api/admin/dashboard", { headers: authHeaders(token) }),

  runCrawler: (token: string) =>
    request<{ message: string }>("/api/admin/crawler/run", {
      method: "POST",
      headers: authHeaders(token),
    }),

  getPendingCourses: (token: string) =>
    request<Course[]>("/api/admin/courses/pending", { headers: authHeaders(token) }),

  getReadyCourses: (token: string) =>
    request<Course[]>("/api/admin/courses/ready", { headers: authHeaders(token) }),

  setAffiliateLink: (token: string, courseId: string, affiliateLink: string) =>
    request<Course>(`/api/admin/courses/${courseId}/affiliate`, {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify({ affiliate_link: affiliateLink }),
    }),

  publishToday: (token: string) =>
    request<PostFull>("/api/admin/posts/publish-today", {
      method: "POST",
      headers: authHeaders(token),
    }),

  getLogs: (token: string) =>
    request<LogEntry[]>("/api/admin/logs", { headers: authHeaders(token) }),

  deleteCourse: (token: string, id: string) =>
    request<{ ok: boolean }>(`/api/admin/courses/${id}`, {
      method: "DELETE",
      headers: authHeaders(token),
    }),

  // Promoter / Categories
  getAdminCategories: (token: string) =>
    request<CategoryItem[]>("/api/admin/categories", { headers: authHeaders(token) }),

  createCategory: (token: string, data: CategoryCreate) =>
    request<CategoryItem>("/api/admin/categories", {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify(data),
    }),

  updateCategory: (token: string, id: string, data: Partial<CategoryCreate>) =>
    request<CategoryItem>(`/api/admin/categories/${id}`, {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify(data),
    }),

  deleteCategory: (token: string, id: string) =>
    request<{ ok: boolean }>(`/api/admin/categories/${id}`, {
      method: "DELETE",
      headers: authHeaders(token),
    }),

  setCourseCategory: (token: string, courseId: string, categoryId: string | null) =>
    request<Course>(`/api/admin/courses/${courseId}/category`, {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify({ category_id: categoryId }),
    }),

  runPromoter: (token: string) =>
    request<{ message: string }>("/api/admin/promoter/run", {
      method: "POST",
      headers: authHeaders(token),
    }),

  getPromotionLogs: (token: string) =>
    request<PromotionLogItem[]>("/api/admin/promotion-logs", { headers: authHeaders(token) }),

  searchTelegram: (token: string, keyword: string) =>
    request<TelegramChannel[]>("/api/admin/search-telegram", {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ keyword }),
    }),
};
