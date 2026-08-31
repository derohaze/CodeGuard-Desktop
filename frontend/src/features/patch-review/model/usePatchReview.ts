import { useEffect, useState } from "react";
import type { RemediationPlan } from "@/entities/finding/model/types";

export function usePatchReview(plan?: RemediationPlan | null) {
  const [reviewState, setReviewState] = useState<"idle" | "applying" | "applied" | "rejected" | "retrying" | "rolling_back" | "rolled_back">("idle");
  const [pendingAction, setPendingAction] = useState<"approve" | "reject" | "retry" | "rollback" | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isReviewDetailsVisible, setIsReviewDetailsVisible] = useState(true);
  const initialDraft = plan?.patch?.afterSnippet ?? "";
  const [draftCode, setDraftCode] = useState(initialDraft);
  const [selectedVariant, setSelectedVariant] = useState(selectDefaultVariant(plan));

  const selectedSuggestion =
    plan?.strategies.find((suggestion) => suggestion.id === selectedVariant) ??
    plan?.strategies[0] ??
    null;

  useEffect(() => {
    const nextRecommended = selectDefaultVariant(plan);
    setSelectedVariant(nextRecommended);
    setReviewState("idle");
    setPendingAction(null);
    setIsEditing(false);
  }, [plan]);

  useEffect(() => {
    setDraftCode(plan?.patch?.afterSnippet ?? "");
  }, [plan?.patch?.afterSnippet]);

  useEffect(() => {
    if (isEditing) return;
    if (!selectedSuggestion?.diff?.trim()) {
      setDraftCode(plan?.patch?.afterSnippet ?? "");
      return;
    }
    const derivedSnippet = deriveSnippetFromDiff(selectedSuggestion.diff);
    setDraftCode(derivedSnippet || (plan?.patch?.afterSnippet ?? ""));
  }, [isEditing, plan?.patch?.afterSnippet, selectedSuggestion?.diff]);

  return {
    draftCode,
    isEditing,
    isReviewDetailsVisible,
    pendingAction,
    reviewState,
    selectedSuggestion,
    selectedVariant,
    setDraftCode,
    setIsEditing,
    setIsReviewDetailsVisible,
    setPendingAction,
    setReviewState,
    setSelectedVariant,
  };
}

function selectDefaultVariant(plan?: RemediationPlan | null) {
  const strategies = plan?.strategies ?? [];
  const recommended = strategies.find((strategy) => strategy.id === plan?.recommendedStrategyId)
    ?? strategies.find((strategy) => strategy.recommended)
    ?? null;
  if (recommended?.policyCompliant) {
    return recommended.id;
  }
  const firstCompliant = strategies.find((strategy) => strategy.policyCompliant);
  if (firstCompliant) {
    return firstCompliant.id;
  }
  return recommended?.id ?? strategies[0]?.id ?? "recommended";
}

function deriveSnippetFromDiff(diff: string) {
  const lines: string[] = [];
  for (const rawLine of diff.split("\n")) {
    if (rawLine.startsWith("---") || rawLine.startsWith("+++") || rawLine.startsWith("@@")) {
      continue;
    }
    if (rawLine.startsWith("+") && !rawLine.startsWith("+++")) {
      lines.push(rawLine.slice(1));
    }
  }
  return lines.join("\n");
}
