export function toAnalystCopy(text: string | null | undefined): string {
  if (!text) return "";

  return [
    [/\[Security Scan\]/g, "[Security Analyst]"],
    [/\bSecurity Scan\b/g, "Security Analyst"],
    [/\bsecurity scan\b/g, "security analyst"],
    [/\bSecurity scan\b/g, "Security analyst"],
    [/\bscan sessions\b/g, "analyst sessions"],
    [/\bscan session\b/g, "analyst session"],
    [/\bDeep Scan\b/g, "Deep analysis"],
    [/\bFast Scan\b/g, "Fast analysis"],
    [/\bdeep scan\b/g, "deep analysis"],
    [/\bfast scan\b/g, "fast analysis"],
    [/\bScan completed\b/g, "Analysis completed"],
    [/\bScan failed\b/g, "Analysis failed"],
    [/\bscan completed\b/g, "analysis completed"],
    [/\bscan failed\b/g, "analysis failed"],
    [/\bScanning\b/g, "Analyzing"],
    [/\bscanning\b/g, "analyzing"],
    [/\breal scan evidence\b/g, "real analysis evidence"],
    [/\breal scan result\b/g, "real analysis result"],
    [/\breal scan trace\b/g, "real analysis trace"],
    [/^Scan\s+/g, "Analyst "],
  ].reduce((current, [pattern, replacement]) => current.replace(pattern, replacement), text);
}
