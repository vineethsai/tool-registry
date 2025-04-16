
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shield, Plus, Search } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { getPolicies } from "@/lib/api";
import { Policy } from "@/lib/types";

export default function Policies() {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const pageSize = 10;

  const { data, isLoading, error } = useQuery({
    queryKey: ["policies", page, pageSize],
    queryFn: () => getPolicies(page, pageSize),
  });

  const renderPolicyList = () => {
    if (isLoading) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10">
            Loading policies...
          </TableCell>
        </TableRow>
      );
    }

    if (error) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10 text-red-500">
            Error loading policies. Please try again.
          </TableCell>
        </TableRow>
      );
    }

    if (!data?.items.length) {
      return (
        <TableRow>
          <TableCell colSpan={5} className="text-center py-10">
            No policies found.
          </TableCell>
        </TableRow>
      );
    }

    return data.items.map((policy) => (
      <TableRow key={policy.policy_id}>
        <TableCell className="font-medium">{policy.name}</TableCell>
        <TableCell>{policy.description}</TableCell>
        <TableCell>
          <div className="flex flex-wrap gap-1">
            {policy.allowed_scopes.map((scope) => (
              <Badge key={scope} variant="outline">{scope}</Badge>
            ))}
          </div>
        </TableCell>
        <TableCell>{policy.priority}</TableCell>
        <TableCell className="text-right">
          <Button variant="ghost" size="sm" asChild>
            <a href={`/policies/${policy.policy_id}`}>View</a>
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
            <Shield className="h-6 w-6 mr-2 text-purple-600" />
            <h1 className="text-2xl font-bold">Policies</h1>
          </div>
          <Button asChild>
            <a href="/policies/new">
              <Plus className="h-4 w-4 mr-2" />
              Create Policy
            </a>
          </Button>
        </div>

        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle>Policy Management</CardTitle>
            <CardDescription>
              Create and manage access policies for tools in the registry.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center mb-4">
              <div className="relative w-full max-w-sm">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                <Input
                  type="search"
                  placeholder="Search policies..."
                  className="pl-8"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Allowed Scopes</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {renderPolicyList()}
                </TableBody>
              </Table>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between">
            <div className="text-sm text-gray-600">
              {data ? `Showing ${(page - 1) * pageSize + 1} to ${Math.min(page * pageSize, data.total)} of ${data.total} policies` : ''}
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
