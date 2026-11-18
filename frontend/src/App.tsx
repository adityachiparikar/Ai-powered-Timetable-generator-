
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";


import Timetables from "@/pages/Timetables";
import DataEntry from "@/pages/DataEntry";
import Constraints from "@/pages/Constraints";
import Settings from "@/pages/Settings";

import Dashboard from "@/pages/Dashboard";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="timetables" element={<Timetables />} />
          <Route path="teachers" element={<Navigate to="/data-entry?tab=teachers" replace />} />
          <Route path="constraints" element={<Constraints />} />
          <Route path="settings" element={<Settings />} />

          {/* Redirect legacy master data routes to DataEntry for now or keep separate if implemented */}
          <Route path="data-entry" element={<DataEntry />} />
          <Route path="courses" element={<Navigate to="/data-entry?tab=courses" replace />} />
          <Route path="rooms" element={<Navigate to="/data-entry?tab=rooms" replace />} />
          <Route path="student-groups" element={<Navigate to="/data-entry?tab=student-groups" replace />} />

          <Route path="*" element={<div>Not Found</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
