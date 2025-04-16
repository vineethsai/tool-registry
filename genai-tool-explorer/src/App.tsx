
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import Policies from "./pages/Policies";
import Agents from "./pages/Agents";
import Access from "./pages/Access";
import Analytics from "./pages/Analytics";
import Tools from "./pages/Tools";
import ToolDetail from "./pages/ToolDetail";
import PolicyDetail from "./pages/PolicyDetail";
import AgentDetail from "./pages/AgentDetail";
import RegisterTool from "./pages/RegisterTool";
import CreatePolicy from "./pages/CreatePolicy";
import RegisterAgent from "./pages/RegisterAgent";
import RequestAccess from "./pages/RequestAccess";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/tools/:toolId" element={<ToolDetail />} />
          <Route path="/tools/new" element={<RegisterTool />} />
          <Route path="/policies" element={<Policies />} />
          <Route path="/policies/:policyId" element={<PolicyDetail />} />
          <Route path="/policies/new" element={<CreatePolicy />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/agents/:agentId" element={<AgentDetail />} />
          <Route path="/agents/new" element={<RegisterAgent />} />
          <Route path="/access" element={<Access />} />
          <Route path="/access/request" element={<RequestAccess />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
