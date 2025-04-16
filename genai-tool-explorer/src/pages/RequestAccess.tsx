import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Key, Shield, Wrench, UserRound, Bot, Server } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";
import { getTools, getPolicies, getAgents, requestAccess } from "@/lib/api";

const formSchema = z.object({
  agent_id: z.string().min(1, {
    message: "Agent is required.",
  }),
  tool_id: z.string().min(1, {
    message: "Tool is required.",
  }),
  policy_id: z.string().min(1, {
    message: "Policy is required.",
  }),
  justification: z.string().min(10, {
    message: "Justification must be at least 10 characters.",
  }),
});

type FormValues = z.infer<typeof formSchema>;

export default function RequestAccess() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedToolId = searchParams.get("tool_id");
  const preselectedAgentId = searchParams.get("agent_id");
  const preselectedPolicyId = searchParams.get("policy_id");

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      agent_id: preselectedAgentId || "",
      tool_id: preselectedToolId || "",
      policy_id: preselectedPolicyId || "",
      justification: "",
    },
  });

  const { data: tools } = useQuery({
    queryKey: ["tools-list"],
    queryFn: () => getTools(1, 100),
  });

  const { data: agents } = useQuery({
    queryKey: ["agents-list"],
    queryFn: () => getAgents(1, 100),
  });

  const { data: policies, refetch: refetchPolicies } = useQuery({
    queryKey: ["policies-list", form.watch("tool_id")],
    queryFn: () => getPolicies(1, 100, form.watch("tool_id")),
    enabled: !!form.watch("tool_id"),
  });

  useEffect(() => {
    if (form.watch("tool_id")) {
      refetchPolicies();
      if (!preselectedPolicyId) {
        form.setValue("policy_id", "");
      }
    }
  }, [form.watch("tool_id"), refetchPolicies, form, preselectedPolicyId]);

  const mutation = useMutation({
    mutationFn: requestAccess,
    onSuccess: (data) => {
      toast({
        title: "Access request submitted",
        description: `Status: ${data.status}`,
      });
      navigate("/access");
    },
    onError: (error: any) => {
      toast({
        title: "Failed to submit access request",
        description: error.message || "An unknown error occurred",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (values: FormValues) => {
    mutation.mutate({
      agent_id: values.agent_id,
      tool_id: values.tool_id,
      policy_id: values.policy_id,
      justification: values.justification
    });
  };

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

  return (
    <MainLayout>
      <div className="container mx-auto py-6">
        <Button
          variant="ghost"
          className="mb-4"
          onClick={() => navigate("/access")}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Access Requests
        </Button>

        <div className="flex items-center mb-6">
          <Key className="h-6 w-6 mr-2 text-purple-600" />
          <h1 className="text-2xl font-bold">Request Tool Access</h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Access Request</CardTitle>
            <CardDescription>
              Request access for an agent to use a specific tool under a policy.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="agent_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Agent</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                        disabled={!!preselectedAgentId}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select agent" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {agents?.items.map((agent) => (
                            <SelectItem key={agent.agent_id} value={agent.agent_id}>
                              <div className="flex items-center">
                                {getAgentTypeIcon(agent.agent_type)}
                                <span className="ml-2">{agent.name}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        The agent that needs access to the tool.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="tool_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tool</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                        disabled={!!preselectedToolId}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select tool" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {tools?.items.map((tool) => (
                            <SelectItem key={tool.tool_id} value={tool.tool_id}>
                              <div className="flex items-center">
                                <Wrench className="h-4 w-4 text-blue-500 mr-2" />
                                <span>{tool.name}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        The tool to request access for.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="policy_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Policy</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                        disabled={!!preselectedPolicyId || !form.watch("tool_id") || !policies?.items.length}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder={
                              !form.watch("tool_id")
                                ? "Select a tool first"
                                : policies?.items.length
                                  ? "Select policy"
                                  : "No policies available for this tool"
                            } />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {policies?.items.map((policy) => (
                            <SelectItem key={policy.policy_id} value={policy.policy_id}>
                              <div className="flex items-center">
                                <Shield className="h-4 w-4 text-purple-500 mr-2" />
                                <span>{policy.name}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        The access policy to apply.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="justification"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Justification</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Explain why this agent needs access to the tool..."
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Provide a clear reason why this access is needed.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate("/access")}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? "Submitting..." : "Submit Request"}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
