import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../services/api';
import { Filter } from 'lucide-react';
import toast from 'react-hot-toast';

function Tasks() {
  const [status, setStatus] = useState('');
  const queryClient = useQueryClient();
  const { data: tasks, isLoading } = useQuery(['tasks', status], () => api.get(`/api/tasks${status ? `?status=${status}` : ''}`).then(r => r.data));

  const updateTask = useMutation(({ id, payload }) => api.put(`/api/tasks/${id}`, payload), {
    onSuccess: () => {
      queryClient.invalidateQueries(['tasks']);
      toast.success('Task updated');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to update task')
  });

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
          <p className="mt-1 text-sm text-gray-500">Filter and manage tasks</p>
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="border border-gray-300 rounded px-2 py-1 text-sm">
            <option value="">All</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
        {tasks?.map((t) => (
          <div key={t.id} className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">{t.title}</p>
              <p className="text-xs text-gray-500">{t.project_name} • {t.assignee_name || 'Unassigned'}</p>
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={t.status}
                onChange={(e) => updateTask.mutate({ id: t.id, payload: { status: e.target.value } })}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
              </select>
            </div>
          </div>
        ))}
        {(!tasks || tasks.length === 0) && (
          <div className="p-6 text-center text-gray-500 text-sm">No tasks found</div>
        )}
      </div>
    </div>
  );
}

export default Tasks;
