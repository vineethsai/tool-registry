
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Users, Bot, UserRound, Server, Plus, Search } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getAgents } from "@/lib/api";

export default function Agents() {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [agentType, setAgentType] = useState<string>("");
  const pageSize = 10;

  const { data, isLoading, error } = useQuery({
    queryKey: ["agents", page, pageSize, agentType],
    queryFn: () => getAgents(page, pageSize, agentType || undefined),
  });

  const getAgentTypeIcon = (type: string) => {
    switch (type) {
      case "user":
        return <UserRound className="h-4 w-4 text-blue-500" />;
      case "service":
        return <Server className="h-4 w-4 text-green-500" />;
      case "bot":
        return <Bot className="h-4 w-4 text-purple-500" />;
      default:
        return <UserRound className="h-4 w-4 text-gray-500" />;
    }
  };

  const renderAgentList = () => {
    if (isLoading) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10">
            Loading agents...
          </TableCell>
        </TableRow>
      );
    }

    if (error) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10 text-red-500">
            Error loading agents. Please try again.
          </TableCell>
        </TableRow>
      );
    }

    if (!data?.items.length) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10">
            No agents found.
          </TableCell>
        </TableRow>
      );
    }

    return data.items.map((agent) => (
      <TableRow key={agent.agent_id}>
        <TableCell className="font-medium">{agent.name}</TableCell>
        <TableCell>{agent.description}</TableCell>
        <TableCell>
          <div className="flex items-center">
            {getAgentTypeIcon(agent.agent_type)}
            <span className="ml-2 capitalize">{agent.agent_type}</span>
          </div>
        </TableCell>
        <TableCell>{new Date(agent.created_at).toLocaleDateString()}</TableCell>
        <TableCell className="text-right">
          <Button variant="ghost" size="sm" asChild>
            <a href={`/agents/${agent.agent_id}`}>View</a>
          </Button>
        </TableCell>
      </TableRow>
    ));
  };

  return (
    <MainLayout>
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <Users className="h-6 w-6 mr-2 text-purple-600" />
            <h1 className="text-2xl font-bold">Agents</h1>
          </div>
          <Button asChild>
            <a href="/agents/new">
              <Plus className="h-4 w-4 mr-2" />
              Register Agent
            </a>
          </Button>
        </div>

        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle>Agent Management</CardTitle>
            <CardDescription>
              Register and manage GenAI agents that need access to tools.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 mb-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                <Input
                  type="search"
                  placeholder="Search agents..."
                  className="pl-8"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Select value={agentType} onValueChange={setAgentType}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="service">Service</SelectItem>
                  <SelectItem value="bot">Bot</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {renderAgentList()}
                </TableBody>
              </Table>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <div className="text-sm text-gray-600">
              {data ? `Showing ${(page - 1) * pageSize + 1} to ${Math.min(page * pageSize, data.total)} of ${data.total} agents` : ''}
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={() => setPage(p => Math.max(p - 1, 1))}
                disabled={page === 1 || isLoading}
              >
                Previous
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setPage(p => p + 1)}
                disabled={!data || page >= data.pages || isLoading}
              >
                Next
              </Button>
            </div>
          </CardFooter>
        </Card>
      </div>
    </MainLayout>
  );
}
