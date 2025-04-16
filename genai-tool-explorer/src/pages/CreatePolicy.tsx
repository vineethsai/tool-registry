import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Shield, Plus, Wrench } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "@/hooks/use-toast";
import { createPolicy, getTools } from "@/lib/api";

const formSchema = z.object({
  name: z.string().min(3, {
    message: "Policy name must be at least 3 characters.",
  }),
  description: z.string().min(10, {
    message: "Description must be at least 10 characters.",
  }),
  tool_id: z.string().min(1, {
    message: "Tool is required.",
  }),
  allowed_scopes: z.array(z.string()).min(1, {
    message: "At least one scope is required.",
  }),
  conditions: z.object({
    max_requests_per_day: z.number().optional(),
    allowed_hours: z.object({
      start: z.string().optional(),
      end: z.string().optional(),
    }).optional(),
  }),
  rules: z.object({
    require_approval: z.boolean(),
    log_usage: z.boolean(),
  }),
  priority: z.number().min(1).max(100),
});

type FormValues = z.infer<typeof formSchema>;

const scopeOptions = [
  { id: "read", label: "Read" },
  { id: "write", label: "Write" },
  { id: "execute", label: "Execute" },
  { id: "admin", label: "Admin" },
];

export default function CreatePolicy() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedToolId = searchParams.get("tool_id");
  const [timeRestrictionEnabled, setTimeRestrictionEnabled] = useState(false);
  
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      tool_id: preselectedToolId || "",
      allowed_scopes: [],
      conditions: {
        max_requests_per_day: 1000,
        allowed_hours: {
          start: "09:00",
          end: "17:00",
        },
      },
      rules: {
        require_approval: false,
        log_usage: true,
      },
      priority: 10,
    },
  });

  const { data: tools } = useQuery({
    queryKey: ["tools-list"],
    queryFn: () => getTools(1, 100),
  });

  const mutation = useMutation({
    mutationFn: createPolicy,
    onSuccess: (data) => {
      toast({
        title: "Policy created successfully",
        description: `${data.name} has been added to the registry.`,
      });
      navigate(`/policies/${data.policy_id}`);
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create policy",
        description: error.message || "An unknown error occurred",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (values: FormValues) => {
    const policyData: Omit<Policy, 'policy_id' | 'created_at' | 'updated_at'> = {
      name: values.name,
      description: values.description,
      tool_id: values.tool_id,
      allowed_scopes: values.allowed_scopes,
      rules: {
        require_approval: Boolean(values.rules.require_approval),
        log_usage: Boolean(values.rules.log_usage),
      },
      priority: values.priority,
      conditions: {
        max_requests_per_day: values.conditions.max_requests_per_day || 0,
      }
    };
    
    if (timeRestrictionEnabled && 
        values.conditions.allowed_hours?.start && 
        values.conditions.allowed_hours?.end) {
      policyData.conditions.allowed_hours = {
        start: values.conditions.allowed_hours.start,
        end: values.conditions.allowed_hours.end
      };
    }
    
    mutation.mutate(policyData);
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

        <div className="flex items-center mb-6">
          <Shield className="h-6 w-6 mr-2 text-purple-600" />
          <h1 className="text-2xl font-bold">Create New Policy</h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Policy Information</CardTitle>
            <CardDescription>
              Define access rules and restrictions for a tool.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Policy Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Basic Access" {...field} />
                      </FormControl>
                      <FormDescription>
                        A descriptive name for this policy.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Basic access to the tool with rate limiting..."
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Describe what this policy allows and any restrictions.
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
                        The tool this policy applies to.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="allowed_scopes"
                  render={() => (
                    <FormItem>
                      <div className="mb-4">
                        <FormLabel className="text-base">Allowed Scopes</FormLabel>
                        <FormDescription>
                          Select what operations this policy allows.
                        </FormDescription>
                      </div>
                      <div className="space-y-2">
                        {scopeOptions.map((scope) => (
                          <FormField
                            key={scope.id}
                            control={form.control}
                            name="allowed_scopes"
                            render={({ field }) => {
                              return (
                                <FormItem
                                  key={scope.id}
                                  className="flex flex-row items-start space-x-3 space-y-0"
                                >
                                  <FormControl>
                                    <Checkbox
                                      checked={field.value?.includes(scope.id)}
                                      onCheckedChange={(checked) => {
                                        const updatedScopes = checked
                                          ? [...field.value, scope.id]
                                          : field.value?.filter(
                                              (value) => value !== scope.id
                                            );
                                        field.onChange(updatedScopes);
                                      }}
                                    />
                                  </FormControl>
                                  <FormLabel className="font-normal">
                                    {scope.label}
                                  </FormLabel>
                                </FormItem>
                              );
                            }}
                          />
                        ))}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="space-y-4 border p-4 rounded-md">
                  <h3 className="font-medium">Conditions</h3>
                  
                  <FormField
                    control={form.control}
                    name="conditions.max_requests_per_day"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Max Requests Per Day</FormLabel>
                        <FormControl>
                          <Input 
                            type="number"
                            min={1}
                            {...field}
                            onChange={(e) => field.onChange(Number(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Rate limiting for this policy (0 = unlimited).
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={timeRestrictionEnabled}
                        onCheckedChange={setTimeRestrictionEnabled}
                        id="time-restriction"
                      />
                      <label
                        htmlFor="time-restriction"
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                        Enable Time Restrictions
                      </label>
                    </div>

                    {timeRestrictionEnabled && (
                      <div className="grid grid-cols-2 gap-4 pt-2">
                        <FormField
                          control={form.control}
                          name="conditions.allowed_hours.start"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Start Time</FormLabel>
                              <FormControl>
                                <Input type="time" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={form.control}
                          name="conditions.allowed_hours.end"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>End Time</FormLabel>
                              <FormControl>
                                <Input type="time" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-4 border p-4 rounded-md">
                  <h3 className="font-medium">Rules</h3>
                  
                  <FormField
                    control={form.control}
                    name="rules.require_approval"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                        <div className="space-y-0.5">
                          <FormLabel>Require Approval</FormLabel>
                          <FormDescription>
                            Access requests will need manual approval.
                          </FormDescription>
                        </div>
                        <FormControl>
                          <Switch
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={form.control}
                    name="rules.log_usage"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                        <div className="space-y-0.5">
                          <FormLabel>Log Usage</FormLabel>
                          <FormDescription>
                            Log all usage of the tool under this policy.
                          </FormDescription>
                        </div>
                        <FormControl>
                          <Switch
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="priority"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Priority</FormLabel>
                      <FormControl>
                        <Input 
                          type="number"
                          min={1}
                          max={100}
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormDescription>
                        Higher priority (1-100) policies are applied first when multiple policies match.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate("/policies")}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? "Creating..." : "Create Policy"}
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
