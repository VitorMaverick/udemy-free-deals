import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import CourseDetail from "./pages/CourseDetail";
import AdminLogin from "./pages/AdminLogin";
import AdminDashboard from "./pages/AdminDashboard";
import CrawlerResults from "./pages/Admin/CrawlerResults";
import ReadyToPublish from "./pages/Admin/ReadyToPublish";
import Logs from "./pages/Admin/Logs";
import Categories from "./pages/Admin/Categories";
import Promoter from "./pages/Admin/Promoter";
import Header from "./components/Header";

export default function App() {
  return (
    <>
      <Header />
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/course/:slug" element={<CourseDetail />} />
          <Route path="/admin" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/admin/crawler-results" element={<CrawlerResults />} />
          <Route path="/admin/ready-to-publish" element={<ReadyToPublish />} />
          <Route path="/admin/categories" element={<Categories />} />
          <Route path="/admin/promoter" element={<Promoter />} />
          <Route path="/admin/logs" element={<Logs />} />
        </Routes>
      </main>
    </>
  );
}
