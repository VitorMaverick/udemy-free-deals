import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import CourseCard from "../components/CourseCard";

export default function Home() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");

  const params: Record<string, string> = { page: String(page), per_page: "20", free_only: "true" };
  if (search) params.search = search;
  if (category) params.category = category;

  const { data, isLoading } = useQuery({
    queryKey: ["courses", params],
    queryFn: () => api.getCourses(params),
  });

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: api.getCategories,
  });

  return (
    <div>
      <section className="mb-6">
        <h1 className="text-2xl font-bold mb-2">🔥 Free Udemy Courses Today</h1>
        <p className="text-gray-600 text-sm">Updated every 6 hours. Grab them before they expire!</p>
      </section>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <input
          type="text"
          placeholder="Search courses..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="border rounded px-3 py-2 text-sm flex-1 min-w-[200px]"
        />
        <select
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          className="border rounded px-3 py-2 text-sm"
          aria-label="Filter by category"
        >
          <option value="">All Categories</option>
          {categories?.map((c) => (
            <option key={c.name} value={c.name}>{c.name} ({c.count})</option>
          ))}
        </select>
      </div>

      {/* Grid */}
      {isLoading ? (
        <p className="text-center py-10 text-gray-500">Loading courses...</p>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
            {data?.items.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
          {data && data.pages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-4 py-2 border rounded disabled:opacity-40"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-sm text-gray-600">
                Page {page} of {data.pages}
              </span>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
                className="px-4 py-2 border rounded disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
          {data?.items.length === 0 && (
            <p className="text-center py-10 text-gray-500">No courses found.</p>
          )}
        </>
      )}
    </div>
  );
}
