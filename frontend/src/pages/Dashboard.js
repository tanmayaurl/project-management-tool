import React from 'react';
import { useQuery } from 'react-query';
import { 
  FolderOpen, 
  CheckSquare, 
  Users, 
  TrendingUp,
  Clock,
  AlertTriangle,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

function Dashboard() {
  const { data: projects, isLoading: projectsLoading } = useQuery(
    'projects',
    () => api.get('/api/projects').then(res => res.data)
  );

  const { data: tasks, isLoading: tasksLoading } = useQuery(
    'tasks',
    () => api.get('/api/tasks').then(res => res.data)
  );

  const { data: myTasks, isLoading: myTasksLoading } = useQuery(
    'my-tasks',
    () => api.get('/api/tasks/my-tasks').then(res => res.data)
  );

  const stats = [
    {
      name: 'Total Projects',
      value: projects?.length || 0,
      icon: FolderOpen,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Total Tasks',
      value: tasks?.length || 0,
      icon: CheckSquare,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'My Tasks',
      value: myTasks?.length || 0,
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      name: 'Completed',
      value: tasks?.filter(task => task.status === 'done').length || 0,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-100',
    },
  ];

  const taskStatusData = [
    { name: 'To Do', value: tasks?.filter(task => task.status === 'todo').length || 0, color: '#6b7280' },
    { name: 'In Progress', value: tasks?.filter(task => task.status === 'in_progress').length || 0, color: '#3b82f6' },
    { name: 'Done', value: tasks?.filter(task => task.status === 'done').length || 0, color: '#10b981' },
  ];

  const projectProgressData = projects?.map(project => ({
    name: project.name,
    progress: project.progress_percentage,
    tasks: project.task_count,
  })) || [];

  const recentTasks = myTasks?.slice(0, 5) || [];
  const overdueTasks = tasks?.filter(task => 
    task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done'
  ) || [];

  if (projectsLoading || tasksLoading || myTasksLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome back! Here's what's happening with your projects.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`p-3 rounded-md ${stat.bgColor}`}>
                    <stat.icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stat.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task Status Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Task Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={taskStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {taskStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Project Progress Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Project Progress</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={projectProgressData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="progress" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Activity and Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Tasks */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Tasks</h3>
          </div>
          <div className="divide-y divide-gray-200">
            {recentTasks.length > 0 ? (
              recentTasks.map((task) => (
                <div key={task.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{task.title}</p>
                      <p className="text-sm text-gray-500">{task.project_name}</p>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium status-${task.status}`}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-4 text-center text-gray-500">
                No recent tasks
              </div>
            )}
          </div>
        </div>

        {/* Overdue Tasks */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
              <h3 className="text-lg font-medium text-gray-900">Overdue Tasks</h3>
            </div>
          </div>
          <div className="divide-y divide-gray-200">
            {overdueTasks.length > 0 ? (
              overdueTasks.map((task) => (
                <div key={task.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{task.title}</p>
                      <p className="text-sm text-gray-500">
                        Due: {new Date(task.due_date).toLocaleDateString()}
                      </p>
                    </div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      Overdue
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-4 text-center text-gray-500">
                <Clock className="h-8 w-8 mx-auto mb-2 text-green-500" />
                No overdue tasks! Great job!
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Features Section */}
      <div className="bg-gradient-to-r from-purple-500 to-blue-600 rounded-lg shadow-lg text-white">
        <div className="px-6 py-8">
          <div className="flex items-center">
            <Sparkles className="h-8 w-8 mr-3" />
            <div>
              <h3 className="text-xl font-bold">AI-Powered Features</h3>
              <p className="text-purple-100 mt-1">
                Generate user stories automatically with our AI assistant
              </p>
            </div>
          </div>
          <div className="mt-4">
            <a
              href="/ai-stories"
              className="inline-flex items-center px-4 py-2 bg-white text-purple-600 rounded-md font-medium hover:bg-purple-50 transition-colors duration-200"
            >
              Try AI Stories
              <Sparkles className="ml-2 h-4 w-4" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
