import React from 'react';
import { useQuery } from 'react-query';
import { api } from '../services/api';

function Users() {
  const { data: users, isLoading, error } = useQuery('users', () => api.get('/api/users').then(r => r.data));

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="spinner"></div></div>;
  if (error) return <div className="text-sm text-red-600">{error.response?.data?.detail || 'Unable to load users'}</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <p className="mt-1 text-sm text-gray-500">System users and roles</p>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users?.map((u) => (
              <tr key={u.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.full_name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.username}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.email}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm capitalize">{u.role}</td>
              </tr>
            ))}
            {(!users || users.length === 0) && (
              <tr><td colSpan={4} className="px-6 py-6 text-center text-sm text-gray-500">No users</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Users;
