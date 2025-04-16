
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Shield, Clock, CalendarDays, Wrench, AlertTriangle } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getPolicy } from "@/lib/api";

export default function PolicyDetail() {
  const { policyId } = useParams<{ policyId: string }>();
  const navigate = useNavigate();

  const { data: policy, isLoading, error } = useQuery({
    queryKey: ["policy", policyId],
    queryFn: () => getPolicy(policyId || ""),
    enabled: !!policyId,
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
          onClick={() => navigate("/policies")}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Policies
        </Button>

        {isLoading ? (
          <div className="text-center py-8">Loading policy details...</div>
        ) : error ? (
          <div className="text-center py-8 text-red-500">
            Error loading policy details. Please try again.
          </div>
        ) : policy ? (
          <div className="space-y-6">
            <div className="flex justify-between items-start">
              <div className="flex items-center">
                <Shield className="h-6 w-6 mr-2 text-purple-600" />
                <h1 className="text-3xl font-bold">{policy.name}</h1>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => navigate(`/policies/edit/${policy.policy_id}`)}>
                  Edit Policy
                </Button>
              </div>
            </div>

            <p className="text-gray-600">{policy.description}</p>

            <div className="flex items-center space-x-4">
              <Badge className="capitalize">Priority: {policy.priority}</Badge>
              <div className="flex items-center text-gray-500">
                <CalendarDays className="h-4 w-4 mr-1" />
                <span>Created: {formatDate(policy.created_at)}</span>
              </div>
              <div className="flex items-center text-gray-500">
                <Clock className="h-4 w-4 mr-1" />
                <span>Updated: {formatDate(policy.updated_at)}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Policy Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Associated Tool</h3>
                    <div className="flex items-center mt-1">
                      <Wrench className="h-4 w-4 mr-1 text-blue-500" />
                      <Button variant="link" className="p-0 h-auto" asChild>
                        <a href={`/tools/${policy.tool_id}`}>{policy.tool_id}</a>
                      </Button>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Allowed Scopes</h3>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {policy.allowed_scopes.map((scope) => (
                        <Badge key={scope} variant="secondary">
                          {scope}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Rules</h3>
                    <div className="mt-1 space-y-2">
                      <div className="flex items-center">
                        <div className={policy.rules.require_approval ? "text-amber-500" : "text-green-500"}>
                          {policy.rules.require_approval ? (
                            <AlertTriangle className="h-4 w-4 inline mr-1" />
                          ) : null}
                          <span>Require Approval: {policy.rules.require_approval ? "Yes" : "No"}</span>
                        </div>
                      </div>
                      <div>
                        Log Usage: {policy.rules.log_usage ? "Yes" : "No"}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Conditions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {policy.conditions.max_requests_per_day && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500">Rate Limiting</h3>
                      <div className="mt-1">
                        Maximum {policy.conditions.max_requests_per_day} requests per day
                      </div>
                    </div>
                  )}
                  
                  {policy.conditions.allowed_hours && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500">Time Restrictions</h3>
                      <div className="mt-1">
                        Allowed between {policy.conditions.allowed_hours.start} and {policy.conditions.allowed_hours.end}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Related Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Button asChild variant="outline" className="w-full">
                    <a href={`/access/request?policy_id=${policy.policy_id}&tool_id=${policy.tool_id}`}>
                      Request Access with this Policy
                    </a>
                  </Button>
                  <Button asChild variant="outline" className="w-full">
                    <a href={`/access?policy_id=${policy.policy_id}`}>
                      View Access Requests
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="text-center py-8">Policy not found</div>
        )}
      </div>
    </MainLayout>
  );
}
