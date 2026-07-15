import { BrowserRouter, Routes, Route } from "react-router-dom"
import { Layout } from "@/components/layout/Layout"
import { HomePage } from "@/pages/HomePage"
import { ConnectedDevicesPage } from "@/pages/ConnectedDevicesPage"
import { TasksPage } from "@/pages/TasksPage"
import { ActivityLogsPage } from "@/pages/ActivityLogsPage"
import { NodeAnalyticsPage } from "@/pages/NodeAnalyticsPage"
import { ModelsPage } from "@/pages/ModelsPage"

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/devices" element={<ConnectedDevicesPage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/activity" element={<ActivityLogsPage />} />
          <Route path="/analytics" element={<NodeAnalyticsPage />} />
          <Route path="/models" element={<ModelsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
