import { cn } from "@/lib/utils";
import { AmazonwebservicesIcon } from "@/components/icons/simple-icons-amazonwebservices";
import { OpenaiIcon } from "@/components/icons/simple-icons-openai";
import { OllamaIcon } from "@/components/icons/simple-icons-ollama";

export type ProviderIconId = "openai" | "bedrock" | "ollama";

export type ProviderIconKind = "openai" | "aws" | "ollama";

const SIZE_MAP = { sm: 20, lg: 32 } as const;

export function providerIconKind(id: ProviderIconId): ProviderIconKind {
  if (id === "bedrock") return "aws";
  if (id === "ollama") return "ollama";
  return "openai";
}

type ProviderIconProps = {
  id: ProviderIconId;
  size?: keyof typeof SIZE_MAP;
  className?: string;
};

export function ProviderIcon({ id, size = "sm", className }: ProviderIconProps) {
  const px = SIZE_MAP[size];
  const iconClass = cn("shrink-0", className);

  if (id === "openai") {
    return <OpenaiIcon size={px} className={iconClass} aria-hidden />;
  }
  if (id === "bedrock") {
    return <AmazonwebservicesIcon size={px} color="#FF9900" className={iconClass} aria-hidden />;
  }
  return <OllamaIcon size={px} className={iconClass} aria-hidden />;
}

export function ProviderIconBadge({ id, size = "sm" }: ProviderIconProps) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-md bg-muted/40",
        size === "lg" ? "size-10" : "size-8",
      )}
      aria-hidden
    >
      <ProviderIcon id={id} size={size} />
    </span>
  );
}
