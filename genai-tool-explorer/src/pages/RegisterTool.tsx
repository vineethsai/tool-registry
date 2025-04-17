import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Plus, Trash2, Tag } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";
import { createTool } from "@/lib/api";

const formSchema = z.object({
  name: z.string().min(3, {
    message: "Tool name must be at least 3 characters.",
  }),
  description: z.string().min(10, {
    message: "Description must be at least 10 characters.",
  }),
  api_endpoint: z.string().url({
    message: "Must be a valid URL.",
  }),
  auth_method: z.enum(["api_key", "oauth2", "jwt", "none"]),
  version: z.string().min(1, {
    message: "Version is required.",
  }),
  tags: z.array(z.string()).min(1, {
    message: "At least one tag is required.",
  }),
  schema_version: z.string().default("1.0"),
  schema_type: z.string().default("openapi"),
  documentation_url: z.string().url().optional().or(z.literal("")),
  provider: z.string().optional().or(z.literal("")),
  inputsDescription: z.string().optional().or(z.literal("")),
  outputsDescription: z.string().optional().or(z.literal(""))
});

type FormValues = z.infer<typeof formSchema>;

export default function RegisterTool() {
  const navigate = useNavigate();
  const [newTag, setNewTag] = useState("");
  
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      api_endpoint: "",
      auth_method: "api_key",
      version: "1.0.0",
      tags: [],
      schema_version: "1.0",
      schema_type: "openapi",
      documentation_url: "",
      provider: "",
      inputsDescription: "",
      outputsDescription: ""
    },
  });

  const mutation = useMutation({
    mutationFn: createTool,
    onSuccess: (data) => {
      toast({
        title: "Tool registered successfully",
        description: `${data.name} has been added to the registry.`,
      });
      navigate(`/tools/${data.tool_id}`);
    },
    onError: (error: any) => {
      toast({
        title: "Failed to register tool",
        description: error.message || "An unknown error occurred",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (values: FormValues) => {
    const inputs: Record<string, any> = {};
    if (values.inputsDescription) {
      inputs["input"] = {
        type: "string",
        description: values.inputsDescription
      };
    }

    const outputs: Record<string, any> = {};
    if (values.outputsDescription) {
      outputs["output"] = {
        type: "string",
        description: values.outputsDescription
      };
    }

    const toolData = {
      name: values.name,
      description: values.description,
      api_endpoint: values.api_endpoint,
      auth_method: values.auth_method,
      version: values.version,
      tags: values.tags,
      auth_config: {
        header_name: "X-API-Key",
        key_placeholder: "${API_KEY}",
      },
      params: {},
      tool_metadata: {
        schema_version: values.schema_version,
        schema_type: values.schema_type,
        schema_data: {},
        inputs: inputs,
        outputs: outputs,
        documentation_url: values.documentation_url || undefined,
        provider: values.provider || undefined,
        tags: values.tags
      }
    };
    
    console.log("Sending tool creation request:", toolData);
    mutation.mutate(toolData);
  };

  const addTag = () => {
    if (newTag.trim() && !form.getValues().tags.includes(newTag.trim())) {
      form.setValue("tags", [...form.getValues().tags, newTag.trim()]);
      setNewTag("");
    }
  };

  const removeTag = (tagToRemove: string) => {
    form.setValue(
      "tags",
      form.getValues().tags.filter((tag) => tag !== tagToRemove)
    );
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

        <div className="flex items-center mb-6">
          <Plus className="h-6 w-6 mr-2 text-purple-600" />
          <h1 className="text-2xl font-bold">Register New Tool</h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Tool Information</CardTitle>
            <CardDescription>
              Provide details about the GenAI tool you want to register.
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
                      <FormLabel>Tool Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Image Generator" {...field} />
                      </FormControl>
                      <FormDescription>
                        A unique name for your tool.
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
                          placeholder="Generates images from text prompts using state-of-the-art AI models"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Describe what the tool does and how it can be used.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="api_endpoint"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>API Endpoint</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="https://api.example.com/generate"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        The URL where the tool's API can be accessed.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField
                    control={form.control}
                    name="auth_method"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Authentication Method</FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          defaultValue={field.value}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select authentication method" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="api_key">API Key</SelectItem>
                            <SelectItem value="oauth2">OAuth 2.0</SelectItem>
                            <SelectItem value="jwt">JWT</SelectItem>
                            <SelectItem value="none">None</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormDescription>
                          How agents will authenticate with the tool.
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="version"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Version</FormLabel>
                        <FormControl>
                          <Input placeholder="1.0.0" {...field} />
                        </FormControl>
                        <FormDescription>
                          The current version of the tool.
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="tags"
                  render={() => (
                    <FormItem>
                      <FormLabel>Tags</FormLabel>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Add a tag"
                          value={newTag}
                          onChange={(e) => setNewTag(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              e.preventDefault();
                              addTag();
                            }
                          }}
                        />
                        <Button type="button" onClick={addTag}>
                          Add
                        </Button>
                      </div>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {form.getValues().tags.map((tag) => (
                          <div
                            key={tag}
                            className="flex items-center bg-purple-100 text-purple-800 px-2 py-1 rounded-md"
                          >
                            <Tag className="h-3.5 w-3.5 mr-1" />
                            {tag}
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="h-4 w-4 p-0 ml-1"
                              onClick={() => removeTag(tag)}
                            >
                              <Trash2 className="h-3 w-3 text-purple-800" />
                            </Button>
                          </div>
                        ))}
                      </div>
                      <FormDescription>
                        Add tags to help agents discover this tool.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="pt-6 border-t-2 border-gray-100">
                  <h3 className="text-lg font-medium mb-4">Tool Metadata</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <FormField
                      control={form.control}
                      name="schema_version"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Schema Version</FormLabel>
                          <FormControl>
                            <Input {...field} />
                          </FormControl>
                          <FormDescription>
                            Version of the schema format
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="schema_type"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Schema Type</FormLabel>
                          <Select
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                          >
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select schema type" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="openapi">OpenAPI</SelectItem>
                              <SelectItem value="jsonschema">JSON Schema</SelectItem>
                              <SelectItem value="custom">Custom</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormDescription>
                            Type of schema the tool uses
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <FormField
                      control={form.control}
                      name="documentation_url"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Documentation URL</FormLabel>
                          <FormControl>
                            <Input placeholder="https://docs.example.com/tool" {...field} />
                          </FormControl>
                          <FormDescription>
                            URL to the tool's documentation
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="provider"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Provider</FormLabel>
                          <FormControl>
                            <Input placeholder="Example Corp" {...field} />
                          </FormControl>
                          <FormDescription>
                            Provider or creator of the tool
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-1 gap-6">
                    <FormField
                      control={form.control}
                      name="inputsDescription"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Input Parameters Description</FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="Describe the inputs required by the tool"
                              {...field}
                            />
                          </FormControl>
                          <FormDescription>
                            Describe what inputs the tool accepts
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="outputsDescription"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Output Format Description</FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="Describe the outputs produced by the tool"
                              {...field}
                            />
                          </FormControl>
                          <FormDescription>
                            Describe what outputs the tool produces
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate("/tools")}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? "Registering..." : "Register Tool"}
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
