
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Wrench, Tag, Shield, Users, Link, FileJson, Clock, Calendar } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getTool } from "@/lib/api";
import { ToolDetails } from "@/lib/types";

export default function ToolDetail() {
  const { toolId } = useParams<{ toolId: string }>();
  const navigate = useNavigate();

  const { data: tool, isLoading, error } = useQuery({
    queryKey: ["tool", toolId],
    queryFn: () => getTool(toolId || ""),
    enabled: !!toolId,
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <MainLayout>
      <div className="container mx-auto py-6">
        <Button
          variant="ghost"
          className="mb-4"
          onClick={() => navigate("/tools")}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Tools
        </Button>

        {isLoading ? (
          <div className="text-center py-8">Loading tool details...</div>
        ) : error ? (
          <div className="text-center py-8 text-red-500">
            Error loading tool details. Please try again.
          </div>
        ) : tool ? (
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between gap-4">
              <div>
                <div className="flex items-center">
                  <Wrench className="h-6 w-6 mr-2 text-purple-600" />
                  <h1 className="text-3xl font-bold">{tool.name}</h1>
                </div>
                <p className="text-gray-600 mt-2">{tool.description}</p>
              </div>
              <div className="flex gap-2">
                <Button asChild>
                  <a href={`/access/request?tool_id=${tool.tool_id}`}>
                    Request Access
                  </a>
                </Button>
                <Button asChild variant="outline">
                  <a href={`/policies/new?tool_id=${tool.tool_id}`}>
                    Create Policy
                  </a>
                </Button>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              {tool.tags.map((tag) => (
                <Badge key={tag} variant="secondary">
                  <Tag className="h-3.5 w-3.5 mr-1" />
                  {tag}
                </Badge>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Tool Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Version</h3>
                    <p>{tool.version}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">API Endpoint</h3>
                    <div className="flex items-center">
                      <Link className="h-4 w-4 mr-1 text-blue-500" />
                      <a
                        href={tool.api_endpoint}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline"
                      >
                        {tool.api_endpoint}
                      </a>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Authentication Method</h3>
                    <p>{tool.auth_method}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Status</h3>
                    <Badge variant={tool.is_active ? "success" : "destructive"}>
                      {tool.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Created</h3>
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-1 text-gray-500" />
                      {formatDate(tool.created_at)}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Updated</h3>
                    <div className="flex items-center">
                      <Clock className="h-4 w-4 mr-1 text-gray-500" />
                      {formatDate(tool.updated_at)}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Parameters</CardTitle>
                  <CardDescription>
                    Input parameters required by this tool
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {Object.keys(tool.params).length === 0 ? (
                    <p className="text-gray-500">No parameters defined</p>
                  ) : (
                    <div className="space-y-4">
                      {Object.entries(tool.params).map(([paramName, paramDetails]) => (
                        <div key={paramName}>
                          <div className="flex items-center">
                            <h3 className="text-sm font-medium">{paramName}</h3>
                            {paramDetails.required && (
                              <Badge variant="destructive" className="ml-2">
                                Required
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-gray-500">{paramDetails.type}</p>
                          {paramDetails.description && (
                            <p className="text-sm mt-1">{paramDetails.description}</p>
                          )}
                          {paramDetails.default !== undefined && (
                            <div className="text-sm mt-1">
                              <span className="text-gray-500">Default:</span>{" "}
                              {paramDetails.default.toString()}
                            </div>
                          )}
                          {paramDetails.allowed_values && (
                            <div className="text-sm mt-1">
                              <span className="text-gray-500">Allowed values:</span>{" "}
                              {paramDetails.allowed_values.join(", ")}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Authentication Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-100 p-4 rounded-md overflow-auto">
                  {JSON.stringify(tool.auth_config, null, 2)}
                </pre>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Policies</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-500 mb-4">
                    Available access policies for this tool
                  </p>
                  <Button asChild variant="outline" className="w-full">
                    <a href={`/policies?tool_id=${tool.tool_id}`}>
                      <Shield className="h-4 w-4 mr-2" />
                      View Policies
                    </a>
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Usage Analytics</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-500 mb-4">
                    View usage statistics and logs for this tool
                  </p>
                  <Button asChild variant="outline" className="w-full">
                    <a href={`/analytics?tool_id=${tool.tool_id}`}>
                      View Analytics
                    </a>
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">Tool not found</div>
        )}
      </div>
    </MainLayout>
  );
}
