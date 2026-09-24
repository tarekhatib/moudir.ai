import type { EmployeeInput } from '../types'

export type EmployeeErrors = Partial<Record<keyof EmployeeInput, string>>

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateEmployee(input: EmployeeInput): EmployeeErrors {
  const errors: EmployeeErrors = {}
  if (!input.name.trim()) errors.name = 'Name is required'
  if (input.email.trim() && !EMAIL_PATTERN.test(input.email.trim())) errors.email = 'Enter a valid email address'
  return errors
}
