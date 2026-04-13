import { useState } from "react";

export function useFindingDetail(onSuggestFix: () => void) {
  const [loading, setLoading] = useState(false);
  const [showAttackerStory, setShowAttackerStory] = useState(false);
  const [showFullAttackerStory, setShowFullAttackerStory] = useState(false);
  const [showAttackSimulation, setShowAttackSimulation] = useState(false);
  const [selectedFixId, setSelectedFixId] = useState("recommended");

  const handleSuggestFix = () => {
    setLoading(true);
    setTimeout(() => {
      onSuggestFix();
    }, 500);
  };

  return {
    handleSuggestFix,
    loading,
    selectedFixId,
    setSelectedFixId,
    setShowAttackSimulation,
    setShowAttackerStory,
    setShowFullAttackerStory,
    showAttackSimulation,
    showAttackerStory,
    showFullAttackerStory,
  };
}
