
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, UserRound, Bot, Server, Clock, Calendar, Key, Wrench } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { getAgent, getCredentials, getAccessRequests } from "@/lib/api";

export default function AgentDetail() {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();

  const { data: agent, isLoading, error } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => getAgent(agentId || ""),
    enabled: !!agentId,
  });

  const { data: credentials } = useQuery({
    queryKey: ["credentials", agentId],
    queryFn: () => getCredentials(1, 10, { agent_id: agentId }),
    enabled: !!agentId,
  });

  const { data: accessRequests } = useQuery({
    queryKey: ["access-requests", agentId],
    queryFn: () => getAccessRequests(1, 10, { agent_id: agentId }),
    enabled: !!agentId,
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const getAgentTypeIcon = (type: string) => {
    switch (type) {
      case "user":
        return <UserRound className="h-5 w-5 text-blue-500" />;
      case "service":
        return <Server className="h-5 w-5 text-green-500" />;
      case "bot":
        return <Bot className="h-5 w-5 text-purple-500" />;
      default:
        return <UserRound className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <MainLayout>
      <div className="container mx-auto py-6">
        <Button
          variant="ghost"
          className="mb-4"
          onClick={() => navigate("/agents")}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Agents
        </Button>

        {isLoading ? (
          <div className="text-center py-8">Loading agent details...</div>
        ) : error ? (
          <div className="text-center py-8 text-red-500">
            Error loading agent details. Please try again.
          </div>
        ) : agent ? (
          <div className="space-y-6">
            <div className="flex justify-between items-start">
              <div className="flex items-center">
                {getAgentTypeIcon(agent.agent_type)}
                <h1 className="text-3xl font-bold ml-2">{agent.name}</h1>
              </div>
              <div className="flex gap-2">
                <Button asChild>
                  <a href={`/access/request?agent_id=${agent.agent_id}`}>
                    Request Access
                  </a>
                </Button>
                <Button variant="outline" onClick={() => navigate(`/agents/edit/${agent.agent_id}`)}>
                  Edit Agent
                </Button>
              </div>
            </div>

            <p className="text-gray-600">{agent.description}</p>

            <div className="flex items-center space-x-4">
              <Badge className="capitalize">{agent.agent_type}</Badge>
              <div className="flex items-center text-gray-500">
                <Calendar className="h-4 w-4 mr-1" />
                <span>Created: {formatDate(agent.created_at)}</span>
              </div>
              <div className="flex items-center text-gray-500">
                <Clock className="h-4 w-4 mr-1" />
                <span>Updated: {formatDate(agent.updated_at)}</span>
              </div>
            </div>

            <Tabs defaultValue="details">
              <TabsList>
                <TabsTrigger value="details">Details</TabsTrigger>
                <TabsTrigger value="credentials">Credentials</TabsTrigger>
                <TabsTrigger value="access">Access Requests</TabsTrigger>
              </TabsList>
              <TabsContent value="details" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Agent Metadata</CardTitle>
                    <CardDescription>
                      Additional information about this agent.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-gray-100 p-4 rounded-md overflow-auto">
                      {JSON.stringify(agent.metadata, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="credentials" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Agent Credentials</CardTitle>
                    <CardDescription>
                      Tool access credentials assigned to this agent.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {credentials?.items.length === 0 ? (
                      <div className="text-center py-4 text-gray-500">
                        No credentials found for this agent.
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {credentials?.items.map((credential) => (
                          <div 
                            key={credential.credential_id} 
                            className="border rounded-md p-4 flex justify-between items-center"
                          >
                            <div>
                              <div className="flex items-center">
                                <Key className="h-4 w-4 mr-2 text-purple-500" />
                                <span className="font-medium">{credential.credential_type}</span>
                              </div>
                              <div className="mt-1 text-sm text-gray-500">
                                <span>Expires: {formatDate(credential.expires_at)}</span>
                              </div>
                            </div>
                            <div className="flex items-center">
                              <Wrench className="h-4 w-4 mr-1" />
                              <span className="text-sm">{credential.tool_id}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="access" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Access Requests</CardTitle>
                    <CardDescription>
                      Tool access requests made by this agent.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {accessRequests?.items.length === 0 ? (
                      <div className="text-center py-4 text-gray-500">
                        No access requests found for this agent.
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {accessRequests?.items.map((request) => (
                          <div 
                            key={request.request_id} 
                            className="border rounded-md p-4"
                          >
                            <div className="flex justify-between">
                              <div className="font-medium">Tool: {request.tool_id}</div>
                              <Badge 
                                variant={
                                  request.status === "approved" 
                                    ? "success" 
                                    : request.status === "rejected" 
                                    ? "destructive" 
                                    : "outline"
                                }
                              >
                                {request.status}
                              </Badge>
                            </div>
                            <div className="mt-2 text-sm">
                              <p className="text-gray-500">Justification:</p>
                              <p>{request.justification}</p>
                            </div>
                            <div className="mt-2 text-sm text-gray-500">
                              Requested: {formatDate(request.created_at)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        ) : (
          <div className="text-center py-8">Agent not found</div>
        )}
      </div>
    </MainLayout>
  );
}
