import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../services/api';
import toast from 'react-hot-toast';

function TaskDetail() {
  const { id } = useParams();
  const taskId = Number(id);
  const queryClient = useQueryClient();
  const [comment, setComment] = useState('');

  const { data: task, isLoading } = useQuery(['task', taskId], () => api.get(`/api/tasks/${taskId}`).then(r => r.data));
  const { data: comments } = useQuery(['task-comments', taskId], () => api.get(`/api/tasks/${taskId}/comments`).then(r => r.data));

  const addComment = useMutation(() => api.post(`/api/tasks/${taskId}/comments`, { content: comment }).then(r => r.data), {
    onSuccess: () => {
      setComment('');
      queryClient.invalidateQueries(['task-comments', taskId]);
      toast.success('Comment added');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to add comment')
  });

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  if (!task) return <div className="text-gray-500">Task not found</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{task.title}</h1>
        <p className="mt-1 text-sm text-gray-500">{task.description || 'No description'}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Comments</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center space-x-2">
                <input
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Add a comment"
                  className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
                />
                <button
                  onClick={() => comment.trim() && addComment.mutate()}
                  className="px-3 py-2 rounded text-white bg-blue-600 hover:bg-blue-700"
                >
                  Add
                </button>
              </div>
              <ul className="divide-y divide-gray-200">
                {comments?.map(c => (
                  <li key={c.id} className="py-3">
                    <p className="text-sm text-gray-800">{c.content}</p>
                    <p className="text-xs text-gray-500">by {c.author_name} • {new Date(c.created_at).toLocaleString()}</p>
                  </li>
                ))}
                {(!comments || comments.length === 0) && (
                  <li className="py-3 text-sm text-gray-500">No comments yet</li>
                )}
              </ul>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Details</h3>
            <div className="text-sm text-gray-700 space-y-1">
              <div>Status: <span className={`px-2 py-0.5 rounded text-xs status-${task.status}`}>{task.status.replace('_', ' ')}</span></div>
              <div>Project: {task.project_name}</div>
              <div>Assignee: {task.assignee_name || 'Unassigned'}</div>
              <div>Creator: {task.creator_name}</div>
              {task.due_date && <div>Due: {new Date(task.due_date).toLocaleDateString()}</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TaskDetail;
