
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Wrench, Tag, Search, Plus } from "lucide-react";
import { MainLayout } from "@/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { getTools, searchTools } from "@/lib/api";
import { ToolCard } from "@/components/tools/ToolCard";
import { useNavigate } from "react-router-dom";

export default function Tools() {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const pageSize = 9;
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery({
    queryKey: ["tools", page, pageSize, selectedTags],
    queryFn: () => searchQuery 
      ? searchTools(searchQuery, page, pageSize) 
      : getTools(page, pageSize, selectedTags.length > 0 ? selectedTags : undefined),
  });

  const handleToolClick = (toolId: string) => {
    navigate(`/tools/${toolId}`);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setPage(1); // Reset to first page on new search
  };

  const handleTagClick = (tag: string) => {
    setSelectedTags(prev => {
      if (prev.includes(tag)) {
        return prev.filter(t => t !== tag);
      } else {
        return [...prev, tag];
      }
    });
    setPage(1); // Reset to first page on tag filter change
  };

  // Collect all unique tags from tools
  const allTags = data?.items.reduce((tags: string[], tool) => {
    tool.tags.forEach(tag => {
      if (!tags.includes(tag)) {
        tags.push(tag);
      }
    });
    return tags;
  }, []) || [];

  return (
    <MainLayout>
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <Wrench className="h-6 w-6 mr-2 text-purple-600" />
            <h1 className="text-2xl font-bold">Tools Registry</h1>
          </div>
          <Button asChild>
            <a href="/tools/new">
              <Plus className="h-4 w-4 mr-2" />
              Register New Tool
            </a>
          </Button>
        </div>

        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle>Tool Management</CardTitle>
            <CardDescription>
              Discover and manage GenAI tools for your agents.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                <Input
                  type="search"
                  placeholder="Search tools..."
                  className="pl-8"
                  value={searchQuery}
                  onChange={handleSearchChange}
                />
              </div>
            </div>

            {allTags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {allTags.map(tag => (
                  <Button
                    key={tag}
                    variant={selectedTags.includes(tag) ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleTagClick(tag)}
                  >
                    <Tag className="h-3.5 w-3.5 mr-1" />
                    {tag}
                  </Button>
                ))}
              </div>
            )}

            {isLoading ? (
              <div className="text-center py-8">Loading tools...</div>
            ) : error ? (
              <div className="text-center py-8 text-red-500">
                Error loading tools. Please try again.
              </div>
            ) : data?.items.length === 0 ? (
              <div className="text-center py-8">
                No tools found. Try adjusting your search or filters.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data?.items.map((tool) => (
                  <ToolCard
                    key={tool.tool_id}
                    tool={tool}
                    onClick={() => handleToolClick(tool.tool_id)}
                  />
                ))}
              </div>
            )}
          </CardContent>
          <CardFooter className="flex justify-between">
            <div className="text-sm text-gray-600">
              {data ? `Showing ${(page - 1) * pageSize + 1} to ${Math.min(page * pageSize, data.total)} of ${data.total} tools` : ''}
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
