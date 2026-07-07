export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export function formatCharacterCount(count: number, limit: number): string {
  return `${count}/${limit} characters`;
}
