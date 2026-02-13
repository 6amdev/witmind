/**
 * Date utilities for handling UTC dates from the API
 */

/**
 * Parse a date string from the API as UTC
 * The API returns dates without timezone suffix, but they are in UTC
 */
export function parseUTCDate(dateStr: string): Date {
  // If the date string doesn't have timezone info, assume UTC
  if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
    return new Date(dateStr + 'Z')
  }
  return new Date(dateStr)
}

/**
 * Format a date to Thai locale string
 */
export function formatThaiDate(dateStr: string): string {
  const date = parseUTCDate(dateStr)
  return date.toLocaleDateString('th-TH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Format relative time (e.g., "5 minutes ago")
 */
export function formatRelativeTime(dateStr: string): string {
  const date = parseUTCDate(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'เมื่อสักครู่'
  if (diffMins < 60) return `${diffMins} นาทีที่แล้ว`
  if (diffHours < 24) return `${diffHours} ชั่วโมงที่แล้ว`
  if (diffDays < 7) return `${diffDays} วันที่แล้ว`

  return date.toLocaleDateString('th-TH', {
    month: 'short',
    day: 'numeric',
  })
}

/**
 * Format date/time for display (local timezone)
 */
export function formatDateTime(dateStr: string): string {
  const date = parseUTCDate(dateStr)
  return date.toLocaleString('th-TH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Format time only (local timezone)
 */
export function formatTime(dateStr: string): string {
  const date = parseUTCDate(dateStr)
  return date.toLocaleTimeString('th-TH', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
