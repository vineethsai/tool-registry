
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Tool } from "@/lib/types";
import { ToolCard } from "@/components/tools/ToolCard";
import { Input } from "@/components/ui/input";
import { Search, Wrench, Shield, Users, Key, BarChart } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getTools } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Index() {
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ["recent-tools"],
    queryFn: () => getTools(1, 3),
  });

  const handleToolClick = (toolId: string) => {
    navigate(`/tools/${toolId}`);
  };

  const featuredCards = [
    {
      title: "Tool Registry",
      description: "Register and discover GenAI tools",
      icon: <Wrench className="h-10 w-10 text-purple-600" />,
      path: "/tools",
      actionText: "Explore Tools",
    },
    {
      title: "Access Policies",
      description: "Define access rules for tools",
      icon: <Shield className="h-10 w-10 text-purple-600" />,
      path: "/policies",
      actionText: "Manage Policies",
    },
    {
      title: "Agents Directory",
      description: "Register and manage agents",
      icon: <Users className="h-10 w-10 text-purple-600" />,
      path: "/agents",
      actionText: "View Agents",
    },
    {
      title: "Access Control",
      description: "Manage access to tools",
      icon: <Key className="h-10 w-10 text-purple-600" />,
      path: "/access",
      actionText: "Access Requests",
    },
    {
      title: "Usage Analytics",
      description: "Monitor tool usage and performance",
      icon: <BarChart className="h-10 w-10 text-purple-600" />,
      path: "/analytics",
      actionText: "View Analytics",
    },
  ];

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-8">
        <div className="text-center space-y-2 max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold tracking-tight">GenAI Tool Registry</h1>
          <p className="text-xl text-gray-600">
            A secure and extensible framework for GenAI agents to discover and utilize external tools
          </p>
        </div>

        <div className="relative max-w-xl mx-auto">
          <Search className="absolute left-3 top-3 h-5 w-5 text-gray-500" />
          <Input
            placeholder="Search tools..."
            className="pl-10 py-6 text-lg"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const target = e.target as HTMLInputElement;
                navigate(`/tools?search=${encodeURIComponent(target.value)}`);
              }
            }}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featuredCards.map((card) => (
            <Card key={card.title} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  {card.icon}
                </div>
                <CardTitle className="text-xl mt-4">{card.title}</CardTitle>
                <CardDescription>{card.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  className="w-full" 
                  onClick={() => navigate(card.path)}
                >
                  {card.actionText}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Recently Added Tools</h2>
            <Button variant="outline" onClick={() => navigate("/tools")}>
              View All Tools
            </Button>
          </div>

          {isLoading ? (
            <div className="text-center py-8">Loading tools...</div>
          ) : data?.items && data.items.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.items.map((tool) => (
                <ToolCard
                  key={tool.tool_id}
                  tool={tool}
                  onClick={() => handleToolClick(tool.tool_id)}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 border rounded-lg">
              <p className="text-gray-500">No tools available yet.</p>
              <Button 
                variant="outline" 
                className="mt-4"
                onClick={() => navigate("/tools/new")}
              >
                Register the First Tool
              </Button>
            </div>
          )}
        </div>

        <div className="mt-12 text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to get started?</h2>
          <div className="flex flex-wrap justify-center gap-4">
            <Button size="lg" onClick={() => navigate("/tools/new")}>
              Register a Tool
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate("/agents/new")}>
              Register an Agent
            </Button>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
