import type { ComplianceSeverity } from '~/types/flow'

export function severityColor(severity: ComplianceSeverity): string {
  const map: Record<ComplianceSeverity, string> = {
    critical: 'red',
    major: 'orange',
    minor: 'yellow',
    none: 'green',
  }
  return map[severity] ?? 'gray'
}

export function severityLabel(severity: ComplianceSeverity): string {
  return severity.charAt(0).toUpperCase() + severity.slice(1)
}

export function formatScore(score: number): string {
  return score.toFixed(1)
}

export function priorityColor(priority: string): string {
  const map: Record<string, string> = {
    high: '#ef4444',
    medium: '#f59e0b',
    low: '#22c55e',
  }
  return map[priority] ?? '#6b7280'
}

export function performanceIcon(performance: string): string {
  const map: Record<string, string> = {
    exceeds: 'star',
    meets: 'check-circle',
    below: 'alert-triangle',
    critical: 'alert-octagon',
  }
  return map[performance] ?? 'help-circle'
}
