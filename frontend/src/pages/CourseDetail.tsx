import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

export default function CourseDetail() {
  const { slug } = useParams<{ slug: string }>();

  const { data: course, isLoading } = useQuery({
    queryKey: ["course", slug],
    queryFn: () => api.getCourse(slug!),
    enabled: !!slug,
  });

  if (isLoading) return <p className="text-center py-10">Loading...</p>;
  if (!course) return <p className="text-center py-10">Course not found.</p>;

  return (
    <div className="max-w-3xl mx-auto">
      <img
        src={course.image_url || "https://via.placeholder.com/750x422?text=No+Image"}
        alt={course.title}
        className="w-full rounded-lg shadow mb-6"
      />
      <h1 className="text-2xl font-bold mb-2">{course.title}</h1>
      <p className="text-gray-600 mb-4">By {course.instructor || "Udemy Instructor"}</p>

      <div className="flex items-center gap-3 mb-6">
        {course.is_free ? (
          <span className="bg-green-500 text-white px-3 py-1 rounded font-bold">FREE</span>
        ) : (
          <span className="bg-orange-500 text-white px-3 py-1 rounded font-bold">
            -{course.discount_percent}% OFF
          </span>
        )}
        {course.original_price > 0 && (
          <span className="text-gray-400 line-through">R${course.original_price.toFixed(2)}</span>
        )}
        <span className="text-sm text-gray-500">⭐ {course.rating.toFixed(1)} ({course.num_reviews} reviews)</span>
      </div>

      <a
        href={api.getRedirectUrl(course.id)}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block bg-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-purple-700 transition-colors"
      >
        🎉 Get This Course Free
      </a>

      {course.description && (
        <div className="mt-8 prose prose-sm max-w-none">
          <h2 className="text-lg font-semibold mb-2">About This Course</h2>
          <p className="text-gray-700">{course.description}</p>
        </div>
      )}
    </div>
  );
}
