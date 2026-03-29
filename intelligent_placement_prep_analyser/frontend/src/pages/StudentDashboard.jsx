
import React, { useEffect, useState } from "react";
import axios from "axios";
import { API_ENDPOINTS } from "../config/api";

export default function StudentDashboard() {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get(API_ENDPOINTS.STUDENT_DASHBOARD)
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Student Dashboard</h2>
      <p>Progress: {data.progress}</p>
      <p>Recommendation: {data.recommendation}</p>
    </div>
  );
}
