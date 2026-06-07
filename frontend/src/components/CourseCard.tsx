import { Link } from "react-router-dom";
import { Course, api } from "../lib/api";

export default function CourseCard({ course }: { course: Course }) {
  return (
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden flex flex-col">
      <img
        src={course.image_url || "https://via.placeholder.com/480x270?text=No+Image"}
        alt={course.title}
        className="w-full h-40 object-cover"
        loading="lazy"
      />
      <div className="p-4 flex flex-col flex-1">
        <Link to={`/course/${course.slug}`} className="font-semibold text-sm hover:text-purple-700 line-clamp-2">
          {course.title}
        </Link>
        <p className="text-xs text-gray-500 mt-1">{course.instructor || "Udemy Instructor"}</p>
        <div className="mt-auto pt-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {course.is_free ? (
              <span className="bg-green-500 text-white text-xs font-bold px-2 py-0.5 rounded">FREE</span>
            ) : (
              <span className="bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded">
                -{course.discount_percent}%
              </span>
            )}
            {course.original_price > 0 && (
              <span className="text-xs text-gray-400 line-through">R${course.original_price.toFixed(2)}</span>
            )}
          </div>
          <a
            href={api.getRedirectUrl(course.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-purple-600 text-white text-xs px-3 py-1.5 rounded hover:bg-purple-700 transition-colors"
          >
            Get Deal
          </a>
        </div>
      </div>
    </div>
  );
}
