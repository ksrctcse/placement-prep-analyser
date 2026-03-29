
import React from "react";
import { BrowserRouter,Routes,Route } from "react-router-dom";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import StaffDashboard from "./pages/StaffDashboard.jsx";

function App(){
return(
<BrowserRouter>
<Routes>
<Route path="/" element={<StudentDashboard/>}/>
<Route path="/staff" element={<StaffDashboard/>}/>
</Routes>
</BrowserRouter>
);
}

export default App;
