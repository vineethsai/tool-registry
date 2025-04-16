
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tool } from "@/lib/types";
import { Calendar } from "lucide-react";

interface ToolCardProps {
  tool: Tool;
  onClick: (toolId: string) => void;
}

export function ToolCard({ tool, onClick }: ToolCardProps) {
  return (
    <Card 
      className="hover:shadow-lg transition-shadow cursor-pointer" 
      onClick={() => onClick(tool.tool_id)}
    >
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-xl">
          {tool.name}
          <span className="text-sm text-muted-foreground">{tool.version}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground mb-4">{tool.description}</p>
        <div className="flex flex-wrap gap-2">
          {tool.tags.map((tag) => (
            <Badge key={tag} variant="secondary">
              {tag}
            </Badge>
          ))}
        </div>
      </CardContent>
      <CardFooter className="text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4" />
          {new Date(tool.created_at).toLocaleDateString()}
        </div>
      </CardFooter>
    </Card>
  );
}
