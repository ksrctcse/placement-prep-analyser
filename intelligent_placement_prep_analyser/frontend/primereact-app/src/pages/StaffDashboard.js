
import React,{useEffect,useState} from "react";
import axios from "axios";

export default function StaffDashboard(){

const [students,setStudents]=useState([])

useEffect(()=>{
axios.get("http://localhost:8000/staff/students-progress")
.then(res=>setStudents(res.data.students))
},[])

return(
<div>
<h2>Staff Dashboard</h2>
{students.map((s,i)=>(
<div key={i}>
{s.name} - {s.department} - Score {s.score}
</div>
))}
</div>
)
}
