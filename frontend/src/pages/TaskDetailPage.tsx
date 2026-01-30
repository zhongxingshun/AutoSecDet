import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Square, RotateCcw, FileJson, FileText, X, Eye } from 'lucide-react'
import { tasksApi, reportsApi } from '@/lib/api'
import { cn, getStatusColor, getRiskLevelColor } from '@/lib/utils'
import toast from 'react-hot-toast'

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const taskId = parseInt(id || '0')
  const [selectedResult, setSelectedResult] = useState<any>(null)

  const { data: taskData, isLoading } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => tasksApi.get(taskId),
    enabled: taskId > 0,
    refetchInterval: (query) => {
      const status = query.state.data?.data?.status
      return status === 'running' || status === 'pending' ? 3000 : false
    },
  })

  const stopMutation = useMutation({
    mutationFn: () => tasksApi.stop(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', taskId] })
      toast.success('任务已停止')
    },
  })

  const retryMutation = useMutation({
    mutationFn: () => tasksApi.retry(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', taskId] })
      toast.success('重试已启动')
    },
  })

  const handleExportJson = async () => {
    try {
      const response = await reportsApi.exportJson(taskId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `report_task_${taskId}.json`
      link.click()
      toast.success('报告已导出')
    } catch {
      toast.error('导出失败')
    }
  }

  const handleExportHtml = async () => {
    try {
      const response = await reportsApi.exportHtml(taskId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `report_task_${taskId}.html`
      link.click()
      toast.success('报告已导出')
    } catch {
      toast.error('导出失败')
    }
  }

  const task = taskData?.data
  const results = task?.results || []

  const getStatusText = (status: string) => {
    const map: Record<string, string> = {
      pending: '等待中',
      running: '运行中',
      completed: '已完成',
      stopped: '已停止',
      error: '错误',
      pass: '通过',
      fail: '失败',
    }
    return map[status] || status
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  if (!task) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">任务不存在</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/tasks')}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">任务 #{task.id}</h1>
            <p className="text-gray-500">目标: {task.target_ip}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {(task.status === 'pending' || task.status === 'running') && (
            <button
              onClick={() => stopMutation.mutate()}
              className="flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50"
            >
              <Square className="h-4 w-4" />
              停止
            </button>
          )}
          {(task.status === 'completed' || task.status === 'error' || task.status === 'stopped') && task.error_count > 0 && (
            <button
              onClick={() => retryMutation.mutate()}
              className="flex items-center gap-2 px-4 py-2 border border-orange-300 text-orange-600 rounded-lg hover:bg-orange-50"
            >
              <RotateCcw className="h-4 w-4" />
              重试失败
            </button>
          )}
          <button
            onClick={handleExportJson}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <FileJson className="h-4 w-4" />
            导出 JSON
          </button>
          <button
            onClick={handleExportHtml}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <FileText className="h-4 w-4" />
            导出报告
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">状态</p>
          <span className={cn('inline-block mt-1 px-2 py-1 text-sm font-medium rounded', getStatusColor(task.status))}>
            {getStatusText(task.status)}
          </span>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">进度</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{task.progress}%</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">通过</p>
          <p className="text-2xl font-bold text-green-600 mt-1">{task.passed_count}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">失败</p>
          <p className="text-2xl font-bold text-red-600 mt-1">{task.failed_count}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500">错误</p>
          <p className="text-2xl font-bold text-yellow-600 mt-1">{task.error_count}</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">执行进度</span>
          <span className="text-sm text-gray-500">{task.completed_cases} / {task.total_cases}</span>
        </div>
        <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-600 transition-all duration-300"
            style={{ width: `${task.progress}%` }}
          />
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">检测结果</h2>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用例</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">分类</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">风险等级</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">错误信息</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {results.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">暂无结果</td>
              </tr>
            ) : (
              results.map((r: any) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{r.case_name || `Case #${r.case_id}`}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{r.category_name || '-'}</td>
                  <td className="px-6 py-4">
                    {r.risk_level && (
                      <span className={cn('px-2 py-1 text-xs font-medium rounded', getRiskLevelColor(r.risk_level))}>
                        {r.risk_level === 'high' ? '高' : r.risk_level === 'medium' ? '中' : '低'}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn('px-2 py-1 text-xs font-medium rounded', getStatusColor(r.status))}>
                      {getStatusText(r.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {r.error_message ? (
                      <button
                        onClick={() => setSelectedResult(r)}
                        className="flex items-center gap-1 text-primary-600 hover:text-primary-700 hover:underline"
                      >
                        <Eye className="h-4 w-4" />
                        查看详情
                      </button>
                    ) : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Detail Modal */}
      {selectedResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{selectedResult.case_name}</h3>
                <p className="text-sm text-gray-500">{selectedResult.category_name}</p>
              </div>
              <button
                onClick={() => setSelectedResult(null)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex-1">
              <div className="flex items-center gap-4 mb-4">
                <div>
                  <span className="text-sm text-gray-500">状态：</span>
                  <span className={cn('ml-2 px-2 py-1 text-xs font-medium rounded', getStatusColor(selectedResult.status))}>
                    {getStatusText(selectedResult.status)}
                  </span>
                </div>
                {selectedResult.risk_level && (
                  <div>
                    <span className="text-sm text-gray-500">风险等级：</span>
                    <span className={cn('ml-2 px-2 py-1 text-xs font-medium rounded', getRiskLevelColor(selectedResult.risk_level))}>
                      {selectedResult.risk_level === 'high' ? '高' : selectedResult.risk_level === 'medium' ? '中' : '低'}
                    </span>
                  </div>
                )}
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">检测结果详情：</h4>
                <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg border overflow-x-auto">
                  {selectedResult.error_message || '无详细信息'}
                </pre>
              </div>
            </div>
            <div className="p-4 border-t flex justify-end">
              <button
                onClick={() => setSelectedResult(null)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
