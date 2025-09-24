import React, { useState, useMemo } from 'react';
import { useQuery, useMutation } from 'react-query';
import { api } from '../services/api';
import { Sparkles, BookOpen, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';

function AIStories() {
  const [projectId, setProjectId] = useState('');
  const [description, setDescription] = useState('');
  const [generated, setGenerated] = useState([]);

  const { data: projects, isLoading: loadingProjects } = useQuery(
    'projects',
    () => api.get('/api/projects').then(res => res.data)
  );

  const storiesMutation = useMutation(
    (payload) => api.post('/api/ai/generate-user-stories', payload).then(res => res.data),
    {
      onSuccess: (data) => {
        setGenerated(data.stories || []);
        toast.success(`Generated ${data.stories?.length || 0} stories`);
      },
      onError: (error) => {
        toast.error(error.response?.data?.detail || 'Failed to generate stories');
      }
    }
  );

  const canSubmit = useMemo(() => !!projectId && description.trim().length > 10, [projectId, description]);

  const handleGenerate = (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    storiesMutation.mutate({ project_description: description, project_id: Number(projectId) });
  };

  const selectedProject = projects?.find(p => String(p.id) === String(projectId));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI User Story Generator</h1>
          <p className="mt-1 text-sm text-gray-500">Use AI to generate actionable user stories from a plain-text description</p>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white rounded-lg shadow p-6">
        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Project</label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="" disabled>{loadingProjects ? 'Loading projects...' : 'Choose a project'}</option>
              {projects?.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Description</label>
            <textarea
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your project goals, users, flows, constraints, and features..."
              className="block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">Tip: Provide details about user types, key actions, and business rules for better stories.</p>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!canSubmit || storiesMutation.isLoading}
              className="inline-flex items-center px-4 py-2 rounded-md text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
            >
              {storiesMutation.isLoading ? (
                <span className="spinner mr-2"></span>
              ) : (
                <Sparkles className="h-4 w-4 mr-2" />
              )}
              Generate Stories
            </button>
          </div>
        </form>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center">
            <BookOpen className="h-5 w-5 text-purple-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Generated Stories</h3>
          </div>
          {selectedProject && (
            <div className="text-sm text-gray-500">Project: <span className="font-medium text-gray-700">{selectedProject.name}</span></div>
          )}
        </div>
        <div className="p-6">
          {generated.length === 0 ? (
            <div className="text-center text-gray-500">No stories yet. Generate to see results.</div>
          ) : (
            <ul className="space-y-3">
              {generated.map((story, idx) => (
                <li key={idx} className="flex items-start">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500 mt-0.5 mr-2" />
                  <span className="text-gray-800">{story}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default AIStories;
