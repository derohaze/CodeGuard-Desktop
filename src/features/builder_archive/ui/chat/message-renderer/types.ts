export interface BuilderDescriptionListEntry {
  details: string;
  term: string;
}

export type BuilderMessageBlock =
  | { type: "code"; code: string; language: string | null }
  | { type: "description-list"; entries: BuilderDescriptionListEntry[] }
  | { type: "heading"; level: 1 | 2 | 3 | 4 | 5 | 6; text: string }
  | { type: "list"; items: string[]; ordered: boolean }
  | { type: "paragraph"; text: string }
  | { type: "separator" }
  | { type: "table"; headers: string[]; rows: string[][] };
