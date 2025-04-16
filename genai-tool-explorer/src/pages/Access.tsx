
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Key, Plus, Clock, CheckCircle, XCircle, Calendar } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { getAccessRequests, getCredentials } from "@/lib/api";

export default function Access() {
  const [page, setPage] = useState(1);
  const [requestStatus, setRequestStatus] = useState<string>("");
  const [activeTab, setActiveTab] = useState("requests");
  const pageSize = 10;

  const { 
    data: requestsData, 
    isLoading: requestsLoading, 
    error: requestsError 
  } = useQuery({
    queryKey: ["access-requests", page, pageSize, requestStatus],
    queryFn: () => getAccessRequests(
      page, 
      pageSize, 
      requestStatus ? { status: requestStatus as any } : undefined
    ),
    enabled: activeTab === "requests",
  });

  const { 
    data: credentialsData, 
    isLoading: credentialsLoading, 
    error: credentialsError 
  } = useQuery({
    queryKey: ["credentials", page, pageSize],
    queryFn: () => getCredentials(page, pageSize),
    enabled: activeTab === "credentials",
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return <Badge className="bg-green-100 text-green-800 hover:bg-green-200 hover:text-green-900">
          <CheckCircle className="mr-1 h-3 w-3" /> Approved
        </Badge>;
      case "rejected":
        return <Badge className="bg-red-100 text-red-800 hover:bg-red-200 hover:text-red-900">
          <XCircle className="mr-1 h-3 w-3" /> Rejected
        </Badge>;
      case "pending":
      default:
        return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-200 hover:text-yellow-900">
          <Clock className="mr-1 h-3 w-3" /> Pending
        </Badge>;
    }
  };

  const renderAccessRequests = () => {
    if (requestsLoading) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10">
            Loading access requests...
          </TableCell>
        </TableRow>
      );
    }

    if (requestsError) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10 text-red-500">
            Error loading access requests. Please try again.
          </TableCell>
        </TableRow>
      );
    }

    if (!requestsData?.items.length) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10">
            No access requests found.
          </TableCell>
        </TableRow>
      );
    }

    return requestsData.items.map((request) => (
      <TableRow key={request.request_id}>
        <TableCell className="font-medium">{request.agent_id}</TableCell>
        <TableCell>{request.tool_id}</TableCell>
        <TableCell>{request.policy_id}</TableCell>
        <TableCell>{getStatusBadge(request.status)}</TableCell>
        <TableCell>{new Date(request.created_at).toLocaleDateString()}</TableCell>
        <TableCell className="text-right">
          <Button variant="ghost" size="sm" asChild>
            <a href={`/access/requests/${request.request_id}`}>View</a>
          </Button>
        </TableCell>
      </TableRow>
    ));
  };

  const renderCredentials = () => {
    if (credentialsLoading) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10">
            Loading credentials...
          </TableCell>
        </TableRow>
      );
    }

    if (credentialsError) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10 text-red-500">
            Error loading credentials. Please try again.
          </TableCell>
        </TableRow>
      );
    }

    if (!credentialsData?.items.length) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10">
            No credentials found.
          </TableCell>
        </TableRow>
      );
    }

    return credentialsData.items.map((credential) => (
      <TableRow key={credential.credential_id}>
        <TableCell className="font-medium">{credential.credential_id}</TableCell>
        <TableCell>{credential.agent_id}</TableCell>
        <TableCell>{credential.tool_id}</TableCell>
        <TableCell>{credential.credential_type}</TableCell>
        <TableCell>
          <div className="flex items-center">
            <Calendar className="mr-1 h-4 w-4 text-gray-500" />
            {new Date(credential.expires_at).toLocaleDateString()}
          </div>
        </TableCell>
        <TableCell className="text-right">
          <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700 hover:bg-red-50">
            Revoke
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
            <Key className="h-6 w-6 mr-2 text-purple-600" />
            <h1 className="text-2xl font-bold">Access Control</h1>
          </div>
          <Button asChild>
            <a href="/access/request">
              <Plus className="h-4 w-4 mr-2" />
              Request Access
            </a>
          </Button>
        </div>

        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle>Access Management</CardTitle>
            <CardDescription>
              Manage access requests and credentials for tools.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="requests" className="w-full" onValueChange={setActiveTab}>
              <TabsList className="mb-4">
                <TabsTrigger value="requests">Access Requests</TabsTrigger>
                <TabsTrigger value="credentials">Credentials</TabsTrigger>
              </TabsList>
              
              <TabsContent value="requests">
                <div className="flex justify-end mb-4">
                  <Select value={requestStatus} onValueChange={setRequestStatus}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Filter by status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="approved">Approved</SelectItem>
                      <SelectItem value="rejected">Rejected</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Agent</TableHead>
                        <TableHead>Tool</TableHead>
                        <TableHead>Policy</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {renderAccessRequests()}
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>
              
              <TabsContent value="credentials">
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Agent</TableHead>
                        <TableHead>Tool</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Expires</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {renderCredentials()}
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
          <CardFooter className="flex justify-between">
            <div className="text-sm text-gray-600">
              {activeTab === "requests" && requestsData 
                ? `Showing ${(page - 1) * pageSize + 1} to ${Math.min(page * pageSize, requestsData.total)} of ${requestsData.total} requests` 
                : activeTab === "credentials" && credentialsData
                ? `Showing ${(page - 1) * pageSize + 1} to ${Math.min(page * pageSize, credentialsData.total)} of ${credentialsData.total} credentials`
                : ''
              }
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={() => setPage(p => Math.max(p - 1, 1))}
                disabled={page === 1 || 
                  (activeTab === "requests" ? requestsLoading : credentialsLoading)}
              >
                Previous
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setPage(p => p + 1)}
                disabled={
                  (activeTab === "requests" 
                    ? !requestsData || page >= requestsData.pages 
                    : !credentialsData || page >= credentialsData.pages) || 
                  (activeTab === "requests" ? requestsLoading : credentialsLoading)
                }
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
