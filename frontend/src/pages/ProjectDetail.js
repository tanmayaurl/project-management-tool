import React, { useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../services/api';
import { Users, CheckSquare, UserPlus } from 'lucide-react';
import toast from 'react-hot-toast';

function ProjectDetail() {
  const { id } = useParams();
  const projectId = Number(id);
  const queryClient = useQueryClient();
  const [memberUserId, setMemberUserId] = useState('');
  const { data: project, isLoading } = useQuery(['project', projectId], () => api.get(`/api/projects/${projectId}`).then(r => r.data));
  const { data: allUsers } = useQuery('users-all', () => api.get('/api/users').then(r => r.data), { enabled: !!project });
  const { data: tasks } = useQuery(['tasks', projectId], () => api.get(`/api/tasks?project_id=${projectId}`).then(r => r.data), { enabled: !!project });

  const addMember = useMutation((payload) => api.post(`/api/projects/${projectId}/members`, payload), {
    onSuccess: () => {
      queryClient.invalidateQueries(['project', projectId]);
      toast.success('Member added');
      setMemberUserId('');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to add member')
  });

  const existingMemberIds = useMemo(() => new Set((project?.member_count > 0 ? [] : []).map(() => -1)), [project]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>
    );
  }
  if (!project) {
    return <div className="text-gray-500">Project not found</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
        <p className="mt-1 text-sm text-gray-500">{project.description || 'No description'}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Tasks */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center">
                <CheckSquare className="h-5 w-5 text-blue-600 mr-2" />
                <h3 className="text-lg font-medium text-gray-900">Tasks</h3>
              </div>
              <Link to="/tasks" className="text-sm text-blue-600 hover:underline">View all</Link>
            </div>
            <div className="p-6">
              {tasks?.length ? (
                <ul className="divide-y divide-gray-200">
                  {tasks.map((t) => (
                    <li key={t.id} className="py-3 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{t.title}</p>
                        <p className="text-xs text-gray-500">{t.project_name}</p>
                      </div>
                      <Link to={`/tasks/${t.id}`} className={`text-xs px-2 py-1 rounded status-${t.status}`}>
                        {t.status.replace('_',' ')}
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-gray-500 text-sm">No tasks yet.</div>
              )}
            </div>
          </div>
        </div>

        {/* Members */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center">
              <Users className="h-5 w-5 text-purple-600 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">Members</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center space-x-2">
                <select
                  value={memberUserId}
                  onChange={(e) => setMemberUserId(e.target.value)}
                  className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none"
                >
                  <option value="">Select user to add</option>
                  {allUsers?.filter(u => !existingMemberIds.has(u.id)).map(u => (
                    <option key={u.id} value={u.id}>{u.full_name} ({u.username})</option>
                  ))}
                </select>
                <button
                  onClick={() => memberUserId && addMember.mutate({ user_id: Number(memberUserId), role: 'member' })}
                  disabled={!memberUserId || addMember.isLoading}
                  className="inline-flex items-center px-3 py-2 rounded-md text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
                >
                  <UserPlus className="h-4 w-4 mr-1" /> Add
                </button>
              </div>
              <p className="text-xs text-gray-500">Project has {project.member_count} member(s).</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProjectDetail;
