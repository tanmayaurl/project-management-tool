import React from 'react';
import { useAuth } from '../contexts/AuthContext';

function Profile() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
        <p className="mt-1 text-sm text-gray-500">Your account details</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div>
            <div className="text-gray-500">Full name</div>
            <div className="text-gray-900 font-medium">{user.full_name}</div>
          </div>
          <div>
            <div className="text-gray-500">Username</div>
            <div className="text-gray-900 font-medium">{user.username}</div>
          </div>
          <div>
            <div className="text-gray-500">Email</div>
            <div className="text-gray-900 font-medium">{user.email}</div>
          </div>
          <div>
            <div className="text-gray-500">Role</div>
            <div className="text-gray-900 font-medium capitalize">{user.role}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;
