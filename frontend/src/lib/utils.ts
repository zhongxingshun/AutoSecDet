import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

export function getRiskLevelColor(level: string): string {
  switch (level) {
    case 'high':
      return 'text-red-600 bg-red-100'
    case 'medium':
      return 'text-yellow-600 bg-yellow-100'
    case 'low':
      return 'text-green-600 bg-green-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'pass':
    case 'completed':
      return 'text-green-600 bg-green-100'
    case 'fail':
    case 'error':
      return 'text-red-600 bg-red-100'
    case 'running':
      return 'text-blue-600 bg-blue-100'
    case 'pending':
      return 'text-gray-600 bg-gray-100'
    case 'stopped':
      return 'text-orange-600 bg-orange-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}
