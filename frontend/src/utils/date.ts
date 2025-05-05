export const formatLastSeen = (dateStr: string | null): string => {
  if (!dateStr) return 'Never seen'
  
  const date = new Date(dateStr)
  const now = new Date()
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
  
  if (diffInHours < 24) {
    return `${Math.round(diffInHours)} hours ago`
  } else {
    const days = Math.floor(diffInHours / 24)
    return `${days} days ago`
  }
}

export const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return 'N/A'
  
  // Try parsing the date
  let date: Date | null = null
  
  // First try direct parsing
  date = new Date(dateStr)
  
  // If that fails, try parsing common SSL certificate date formats
  if (isNaN(date.getTime())) {
    // Try parsing UTC format (common in SSL certs)
    const utcMatch = dateStr.match(/^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})Z?$/)
    if (utcMatch) {
      const [_, year, month, day, hour, minute, second] = utcMatch
      date = new Date(Date.UTC(
        parseInt(year),
        parseInt(month) - 1,
        parseInt(day),
        parseInt(hour),
        parseInt(minute),
        parseInt(second)
      ))
    }
  }
  
  // If we still don't have a valid date, return the original string
  if (!date || isNaN(date.getTime())) {
    return dateStr
  }
  
  // Format the date
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short'
  }).format(date)
}

export const formatPortDate = (dateStr: string | null): string => {
  return formatLastSeen(dateStr)
} 