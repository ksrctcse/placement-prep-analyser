
import React,{useEffect,useState} from "react";
import axios from "axios";

export default function StudentDashboard(){

const [data,setData]=useState({});

useEffect(()=>{
axios.get("http://localhost:8000/student/dashboard")
.then(res=>setData(res.data))
},[])

return(
<div>
<h2>Student Dashboard</h2>
<p>Progress: {data.progress}</p>
<p>Recommendation: {data.recommendation}</p>
</div>
)
}
