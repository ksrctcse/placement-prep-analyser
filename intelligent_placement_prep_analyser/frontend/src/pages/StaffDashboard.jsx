
import React, { useEffect, useState } from "react";
import axios from "axios";
import { API_ENDPOINTS } from "../config/api";

export default function StaffDashboard() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get(API_ENDPOINTS.STAFF_STUDENTS_PROGRESS)
      .then((res) => {
        setStudents(res.data.students);
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
      <h2>Staff Dashboard</h2>
      {students.map((s, i) => (
        <div key={i}>
          {s.name} - {s.department} - Score {s.score}
        </div>
      ))}
    </div>
  );
}
