
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart as BarChartIcon, LineChart as LineChartIcon, CheckCircle, XCircle, Calendar } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { getUsageLogs, getUsageStats } from "@/lib/api";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  Legend, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from "recharts";

export default function Analytics() {
  const [period, setPeriod] = useState<"day" | "week" | "month">("day");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ["usage-stats", period],
    queryFn: () => getUsageStats({ period }),
  });

  const { data: logsData, isLoading: logsLoading } = useQuery({
    queryKey: ["usage-logs", page, pageSize],
    queryFn: () => getUsageLogs(page, pageSize),
  });

  // Colors for the pie chart
  const COLORS = ["#8884d8", "#82ca9d"];

  // Format data for the success/failure pie chart
  const getPieChartData = () => {
    if (!statsData) return [];
    
    return [
      { name: "Successful", value: statsData.successful_requests },
      { name: "Failed", value: statsData.failed_requests }
    ];
  };

  const renderUsageLogs = () => {
    if (logsLoading) {
      return (
        <TableRow>
          <TableCell colSpan={6} className="text-center py-10">
            Loading usage logs...
          </TableCell>
        </TableRow>
      );
    }

    if (!logsData?.items.length) {
      return (
        <TableRow>
          <TableCell colSpan={6} className="text-center py-10">
            No usage logs found.
          </TableCell>
        </TableRow>
      );
    }

    return logsData.items.map((log) => (
      <TableRow key={log.log_id}>
        <TableCell className="font-medium">{log.agent_id}</TableCell>
        <TableCell>{log.tool_id}</TableCell>
        <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
        <TableCell>{log.duration_ms} ms</TableCell>
        <TableCell>
          {log.status === "success" ? 
            <span className="flex items-center text-green-600">
              <CheckCircle className="h-4 w-4 mr-1" /> Success
            </span> : 
            <span className="flex items-center text-red-600">
              <XCircle className="h-4 w-4 mr-1" /> Error
            </span>
          }
        </TableCell>
        <TableCell className="max-w-xs truncate">
          {log.error_message || "-"}
        </TableCell>
      </TableRow>
    ));
  };

  return (
    <MainLayout>
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <BarChartIcon className="h-6 w-6 mr-2 text-purple-600" />
            <h1 className="text-2xl font-bold">Analytics</h1>
          </div>
          <Select value={period} onValueChange={(value: any) => setPeriod(value)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">Daily</SelectItem>
              <SelectItem value="week">Weekly</SelectItem>
              <SelectItem value="month">Monthly</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
              <BarChartIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? "Loading..." : statsData?.total_requests.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                Across all tools
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? "Loading..." : 
                  `${((statsData?.successful_requests || 0) / (statsData?.total_requests || 1) * 100).toFixed(1)}%`}
              </div>
              <p className="text-xs text-muted-foreground">
                {statsLoading ? "" : `${statsData?.successful_requests?.toLocaleString()} successful requests`}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg. Duration</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? "Loading..." : `${statsData?.average_duration_ms.toFixed(1)} ms`}
              </div>
              <p className="text-xs text-muted-foreground">
                Average response time
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed Requests</CardTitle>
              <XCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? "Loading..." : statsData?.failed_requests.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                {statsLoading ? "" : 
                  `${((statsData?.failed_requests || 0) / (statsData?.total_requests || 1) * 100).toFixed(1)}% of total requests`}
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Usage Over Time</CardTitle>
              <CardDescription>
                Requests per {period} over the selected period
              </CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              {statsLoading ? (
                <div className="flex items-center justify-center h-full">
                  <p>Loading chart data...</p>
                </div>
              ) : statsData?.by_period && statsData.by_period.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={statsData.by_period}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="requests" 
                      stroke="#8884d8" 
                      activeDot={{ r: 8 }} 
                      name="Requests"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="success_rate" 
                      stroke="#82ca9d" 
                      yAxisId={1} 
                      name="Success Rate" 
                      unit="%" 
                      scale="band"
                      hide={true} // Only show on demand to avoid clutter
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p>No data available for the selected period</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tool Usage</CardTitle>
              <CardDescription>
                Distribution of requests across tools
              </CardDescription>
            </CardHeader>
            <CardContent className="h-80">
              {statsLoading ? (
                <div className="flex items-center justify-center h-full">
                  <p>Loading chart data...</p>
                </div>
              ) : statsData?.by_tool && statsData.by_tool.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={statsData.by_tool}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="tool_name" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="requests" fill="#8884d8" name="Requests" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p>No data available for the selected period</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Usage Details</CardTitle>
            <CardDescription>
              Detailed logs of tool usage
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="logs">
              <TabsList className="mb-4">
                <TabsTrigger value="logs">Usage Logs</TabsTrigger>
                <TabsTrigger value="summary">Success/Failure Summary</TabsTrigger>
              </TabsList>

              <TabsContent value="logs">
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Agent</TableHead>
                        <TableHead>Tool</TableHead>
                        <TableHead>Timestamp</TableHead>
                        <TableHead>Duration</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Error</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {renderUsageLogs()}
                    </TableBody>
                  </Table>
                </div>

                <div className="flex justify-between items-center mt-4">
                  <div className="text-sm text-gray-600">
                    {logsData ? `Showing ${(page - 1) * pageSize + 1} to ${Math.min(page * pageSize, logsData.total)} of ${logsData.total} logs` : ''}
                  </div>
                  <div className="flex gap-2">
                    <button 
                      className="px-3 py-1 border rounded hover:bg-gray-50"
                      onClick={() => setPage(p => Math.max(p - 1, 1))}
                      disabled={page === 1 || logsLoading}
                    >
                      Previous
                    </button>
                    <button 
                      className="px-3 py-1 border rounded hover:bg-gray-50"
                      onClick={() => setPage(p => p + 1)}
                      disabled={!logsData || page >= logsData.pages || logsLoading}
                    >
                      Next
                    </button>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="summary">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-medium mb-2">Success vs. Failure</h3>
                    <div className="h-72">
                      {statsLoading ? (
                        <div className="flex items-center justify-center h-full">
                          <p>Loading chart data...</p>
                        </div>
                      ) : statsData ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={getPieChartData()}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              outerRadius={80}
                              fill="#8884d8"
                              dataKey="value"
                              label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                            >
                              {getPieChartData().map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <RechartsTooltip />
                            <Legend />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <p>No data available</p>
                        </div>
                      )}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-medium mb-2">Summary Statistics</h3>
                    <div className="space-y-4">
                      <div className="bg-gray-50 p-4 rounded-md">
                        <p className="text-sm text-gray-600">Total Requests</p>
                        <p className="text-lg font-bold">{statsData?.total_requests.toLocaleString() || "Loading..."}</p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-md">
                        <p className="text-sm text-gray-600">Success Rate</p>
                        <p className="text-lg font-bold">
                          {statsLoading ? "Loading..." : 
                            `${((statsData?.successful_requests || 0) / (statsData?.total_requests || 1) * 100).toFixed(1)}%`}
                        </p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-md">
                        <p className="text-sm text-gray-600">Average Response Time</p>
                        <p className="text-lg font-bold">
                          {statsLoading ? "Loading..." : `${statsData?.average_duration_ms.toFixed(1)} ms`}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
