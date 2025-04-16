
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Users, Plus } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { toast } from "@/hooks/use-toast";
import { createAgent } from "@/lib/api";

const formSchema = z.object({
  name: z.string().min(3, {
    message: "Agent name must be at least 3 characters.",
  }),
  description: z.string().min(10, {
    message: "Description must be at least 10 characters.",
  }),
  agent_type: z.enum(["user", "service", "bot"]),
  metadata: z.object({
    team: z.string().optional(),
    department: z.string().optional(),
    capabilities: z.array(z.string()).optional()
  }).optional(),
});

type FormValues = z.infer<typeof formSchema>;

export default function RegisterAgent() {
  const navigate = useNavigate();
  
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      agent_type: "bot",
      metadata: {
        team: "",
        department: "",
        capabilities: []
      },
    },
  });

  const mutation = useMutation({
    mutationFn: createAgent,
    onSuccess: (data) => {
      toast({
        title: "Agent registered successfully",
        description: `${data.name} has been added to the registry.`,
      });
      navigate(`/agents/${data.agent_id}`);
    },
    onError: (error: any) => {
      toast({
        title: "Failed to register agent",
        description: error.message || "An unknown error occurred",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (values: FormValues) => {
    // Clean up empty metadata fields
    const metadata = { ...values.metadata };
    
    if (metadata.team === "") delete metadata.team;
    if (metadata.department === "") delete metadata.department;
    if (!metadata.capabilities || metadata.capabilities.length === 0) delete metadata.capabilities;
    
    // Submit the form with cleaned metadata, ensuring required properties are included
    mutation.mutate({
      name: values.name,
      description: values.description,
      agent_type: values.agent_type,
      metadata: Object.keys(metadata).length > 0 ? metadata : {},
    });
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

        <div className="flex items-center mb-6">
          <Users className="h-6 w-6 mr-2 text-purple-600" />
          <h1 className="text-2xl font-bold">Register New Agent</h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Agent Information</CardTitle>
            <CardDescription>
              Register a new agent that will access tools in the registry.
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
                      <FormLabel>Agent Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Research Assistant" {...field} />
                      </FormControl>
                      <FormDescription>
                        A descriptive name for the agent.
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
                          placeholder="AI assistant designed to help with research tasks..."
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Describe what the agent does and how it will use tools.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="agent_type"
                  render={({ field }) => (
                    <FormItem className="space-y-3">
                      <FormLabel>Agent Type</FormLabel>
                      <FormControl>
                        <RadioGroup
                          onValueChange={field.onChange}
                          defaultValue={field.value}
                          className="flex flex-col space-y-1"
                        >
                          <FormItem className="flex items-center space-x-3 space-y-0">
                            <FormControl>
                              <RadioGroupItem value="user" />
                            </FormControl>
                            <FormLabel className="font-normal">
                              User - Human end user
                            </FormLabel>
                          </FormItem>
                          <FormItem className="flex items-center space-x-3 space-y-0">
                            <FormControl>
                              <RadioGroupItem value="service" />
                            </FormControl>
                            <FormLabel className="font-normal">
                              Service - Backend system or service
                            </FormLabel>
                          </FormItem>
                          <FormItem className="flex items-center space-x-3 space-y-0">
                            <FormControl>
                              <RadioGroupItem value="bot" />
                            </FormControl>
                            <FormLabel className="font-normal">
                              Bot - AI agent or chatbot
                            </FormLabel>
                          </FormItem>
                        </RadioGroup>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="space-y-4 border p-4 rounded-md">
                  <h3 className="font-medium">Metadata (Optional)</h3>
                  
                  <FormField
                    control={form.control}
                    name="metadata.team"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Team</FormLabel>
                        <FormControl>
                          <Input placeholder="Research" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="metadata.department"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Department</FormLabel>
                        <FormControl>
                          <Input placeholder="AI Lab" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="metadata.capabilities"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Capabilities</FormLabel>
                        <FormControl>
                          <Input 
                            placeholder="documentation,search,analysis"
                            value={field.value?.join(',')}
                            onChange={(e) => {
                              const value = e.target.value;
                              field.onChange(
                                value ? value.split(',').map(item => item.trim()) : []
                              );
                            }}
                          />
                        </FormControl>
                        <FormDescription>
                          Comma-separated list of agent capabilities
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate("/agents")}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? "Registering..." : "Register Agent"}
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
