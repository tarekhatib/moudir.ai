import type { Employee } from '../types'

type Props = {
  employees: Employee[]
  selectedId: number | null
  creating: boolean
  onSelect: (id: number) => void
  onAdd: () => void
}

export function EmployeeList({ employees, selectedId, creating, onSelect, onAdd }: Props) {
  return (
    <div className="panel">
      <h2>Employees</h2>
      {employees.length === 0 ? (
        <p className="muted">No employees yet. Add your first one to get started.</p>
      ) : (
        <div className="employee-list">
          {employees.map((employee) => (
            <button
              key={employee.id}
              type="button"
              className={!creating && selectedId === employee.id ? 'employee-item selected' : 'employee-item'}
              onClick={() => onSelect(employee.id)}
            >
              <span>
                {employee.name}
                {employee.role ? <small className="employee-role">{employee.role}</small> : null}
              </span>
              <small>#{employee.id}</small>
            </button>
          ))}
        </div>
      )}
      <button type="button" className="secondary-button" onClick={onAdd} disabled={creating}>
        Add employee
      </button>
    </div>
  )
}
