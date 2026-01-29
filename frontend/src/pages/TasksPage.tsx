import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, Play, Square, RotateCcw, Eye, ChevronDown, ChevronRight } from 'lucide-react'
import { tasksApi, casesApi, categoriesApi } from '@/lib/api'
import { cn, formatDate, getStatusColor } from '@/lib/utils'
import toast from 'react-hot-toast'

export default function TasksPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)
  const [targetIp, setTargetIp] = useState('')
  const [selectedCaseIds, setSelectedCaseIds] = useState<number[]>([])
  const [selectAll, setSelectAll] = useState(true)
  const [expandedCategories, setExpandedCategories] = useState<number[]>([])

  const { data: tasksData, isLoading } = useQuery({
    queryKey: ['tasks', page],
    queryFn: () => tasksApi.list({ page, page_size: 20 }),
    refetchInterval: 5000, // Auto refresh every 5s
  })

  const { data: casesData } = useQuery({
    queryKey: ['cases-for-task'],
    queryFn: () => casesApi.list({ page_size: 100 }),
    enabled: showCreate,
  })

  const { data: categoriesData } = useQuery({
    queryKey: ['categories-for-task'],
    queryFn: () => categoriesApi.list(),
    enabled: showCreate,
  })

  const availableCases = (casesData?.data?.items || []).filter((c: any) => c.is_enabled)
  const categories = categoriesData?.data?.items || []

  // Group cases by category
  const casesByCategory = categories.map((cat: any) => ({
    ...cat,
    cases: availableCases.filter((c: any) => c.category_id === cat.id),
  })).filter((cat: any) => cat.cases.length > 0)

  // Helper functions for category selection
  const getCategorySelectedCount = (categoryId: number) => {
    const categoryCases = availableCases.filter((c: any) => c.category_id === categoryId)
    return categoryCases.filter((c: any) => selectedCaseIds.includes(c.id)).length
  }

  const toggleCategory = (categoryId: number) => {
    if (expandedCategories.includes(categoryId)) {
      setExpandedCategories(expandedCategories.filter(id => id !== categoryId))
    } else {
      setExpandedCategories([...expandedCategories, categoryId])
    }
  }

  const selectAllInCategory = (categoryId: number) => {
    const categoryCaseIds = availableCases
      .filter((c: any) => c.category_id === categoryId)
      .map((c: any) => c.id)
    const newSelected = [...new Set([...selectedCaseIds, ...categoryCaseIds])]
    setSelectedCaseIds(newSelected)
  }

  const clearAllInCategory = (categoryId: number) => {
    const categoryCaseIds = availableCases
      .filter((c: any) => c.category_id === categoryId)
      .map((c: any) => c.id)
    setSelectedCaseIds(selectedCaseIds.filter(id => !categoryCaseIds.includes(id)))
  }

  const selectAllCases = () => {
    setSelectedCaseIds(availableCases.map((c: any) => c.id))
  }

  const clearAllCases = () => {
    setSelectedCaseIds([])
  }

  const createMutation = useMutation({
    mutationFn: (data: { target_ip: string; case_ids?: number[] }) => tasksApi.create(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      setShowCreate(false)
      setTargetIp('')
      toast.success('任务已创建')
      navigate(`/tasks/${response.data.id}`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '创建失败')
    },
  })

  const stopMutation = useMutation({
    mutationFn: (id: number) => tasksApi.stop(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      toast.success('任务已停止')
    },
  })

  const retryMutation = useMutation({
    mutationFn: (id: number) => tasksApi.retry(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      toast.success('重试已启动')
    },
  })

  const tasks = tasksData?.data?.items || []
  const total = tasksData?.data?.total || 0
  const totalPages = Math.ceil(total / 20)

  const validateIp = (ip: string) => {
    const pattern = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
    return pattern.test(ip)
  }

  const getStatusText = (status: string) => {
    const map: Record<string, string> = {
      pending: '等待中',
      running: '运行中',
      completed: '已完成',
      stopped: '已停止',
      error: '错误',
    }
    return map[status] || status
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">任务管理</h1>
          <p className="text-gray-500 mt-1">管理安全检测任务</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="h-5 w-5" />
          新建任务
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="font-medium text-gray-900 mb-4">新建检测任务</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">目标 IP</label>
              <input
                type="text"
                value={targetIp}
                onChange={(e) => setTargetIp(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                placeholder="例如: 192.168.1.100"
              />
              {targetIp && !validateIp(targetIp) && (
                <p className="mt-1 text-sm text-red-600">请输入有效的 IPv4 地址</p>
              )}
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">选择用例</label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectAll}
                    onChange={(e) => {
                      setSelectAll(e.target.checked)
                      if (e.target.checked) setSelectedCaseIds([])
                    }}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  运行所有启用的用例
                </label>
              </div>
              {!selectAll && (
                <div className="border border-gray-300 rounded-lg overflow-hidden">
                  {casesByCategory.length === 0 ? (
                    <p className="text-sm text-gray-500 p-4">暂无可用用例</p>
                  ) : (
                    <>
                      {/* Quick actions */}
                      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b border-gray-200">
                        <span className="text-xs text-gray-500">
                          已选择 {selectedCaseIds.length} / {availableCases.length} 个用例
                        </span>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={selectAllCases}
                            className="text-xs text-primary-600 hover:text-primary-700"
                          >
                            全选
                          </button>
                          <button
                            type="button"
                            onClick={clearAllCases}
                            className="text-xs text-gray-500 hover:text-gray-700"
                          >
                            清空
                          </button>
                        </div>
                      </div>
                      {/* Category panels */}
                      <div className="max-h-64 overflow-y-auto divide-y divide-gray-200">
                        {casesByCategory.map((cat: any) => {
                          const isExpanded = expandedCategories.includes(cat.id)
                          const selectedCount = getCategorySelectedCount(cat.id)
                          const totalCount = cat.cases.length
                          return (
                            <div key={cat.id}>
                              {/* Category header */}
                              <div className="flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 cursor-pointer">
                                <div
                                  className="flex items-center gap-2 flex-1"
                                  onClick={() => toggleCategory(cat.id)}
                                >
                                  {isExpanded ? (
                                    <ChevronDown className="h-4 w-4 text-gray-500" />
                                  ) : (
                                    <ChevronRight className="h-4 w-4 text-gray-500" />
                                  )}
                                  <span className="text-sm font-medium text-gray-700">{cat.name}</span>
                                  <span className={cn(
                                    "text-xs px-1.5 py-0.5 rounded",
                                    selectedCount === totalCount ? "bg-primary-100 text-primary-700" :
                                    selectedCount > 0 ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-500"
                                  )}>
                                    {selectedCount}/{totalCount}
                                  </span>
                                </div>
                                <div className="flex gap-2">
                                  <button
                                    type="button"
                                    onClick={(e) => { e.stopPropagation(); selectAllInCategory(cat.id) }}
                                    className="text-xs text-primary-600 hover:text-primary-700"
                                  >
                                    全选
                                  </button>
                                  <button
                                    type="button"
                                    onClick={(e) => { e.stopPropagation(); clearAllInCategory(cat.id) }}
                                    className="text-xs text-gray-500 hover:text-gray-700"
                                  >
                                    清空
                                  </button>
                                </div>
                              </div>
                              {/* Cases list */}
                              {isExpanded && (
                                <div className="bg-white">
                                  {cat.cases.map((c: any) => (
                                    <label
                                      key={c.id}
                                      className="flex items-center gap-2 px-6 py-2 hover:bg-gray-50 cursor-pointer"
                                    >
                                      <input
                                        type="checkbox"
                                        checked={selectedCaseIds.includes(c.id)}
                                        onChange={(e) => {
                                          if (e.target.checked) {
                                            setSelectedCaseIds([...selectedCaseIds, c.id])
                                          } else {
                                            setSelectedCaseIds(selectedCaseIds.filter(id => id !== c.id))
                                          }
                                        }}
                                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                                      />
                                      <span className="text-sm text-gray-700">{c.name}</span>
                                    </label>
                                  ))}
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => createMutation.mutate({ 
                target_ip: targetIp,
                case_ids: selectAll ? undefined : selectedCaseIds 
              })}
                disabled={!validateIp(targetIp) || createMutation.isPending || (!selectAll && selectedCaseIds.length === 0)}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                <Play className="h-4 w-4" />
                开始检测
              </button>
              <button
                onClick={() => { setShowCreate(false); setTargetIp(''); setSelectedCaseIds([]); setSelectAll(true) }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tasks Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">目标 IP</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">进度</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">结果</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-gray-500">加载中...</td>
              </tr>
            ) : tasks.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-gray-500">暂无任务</td>
              </tr>
            ) : (
              tasks.map((task: any) => (
                <tr key={task.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">#{task.id}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{task.target_ip}</td>
                  <td className="px-6 py-4">
                    <span className={cn('px-2 py-1 text-xs font-medium rounded', getStatusColor(task.status))}>
                      {getStatusText(task.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-600 transition-all"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{task.progress}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className="text-green-600">{task.passed_count}</span>
                    <span className="text-gray-400"> / </span>
                    <span className="text-red-600">{task.failed_count}</span>
                    <span className="text-gray-400"> / </span>
                    <span className="text-gray-600">{task.total_cases}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{formatDate(task.created_at)}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => navigate(`/tasks/${task.id}`)}
                        className="p-2 text-gray-500 hover:text-primary-600 hover:bg-gray-100 rounded"
                        title="查看详情"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      {(task.status === 'pending' || task.status === 'running') && (
                        <button
                          onClick={() => stopMutation.mutate(task.id)}
                          className="p-2 text-gray-500 hover:text-red-600 hover:bg-gray-100 rounded"
                          title="停止"
                        >
                          <Square className="h-4 w-4" />
                        </button>
                      )}
                      {(task.status === 'completed' || task.status === 'error' || task.status === 'stopped') && task.error_count > 0 && (
                        <button
                          onClick={() => retryMutation.mutate(task.id)}
                          className="p-2 text-gray-500 hover:text-orange-600 hover:bg-gray-100 rounded"
                          title="重试失败用例"
                        >
                          <RotateCcw className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <p className="text-sm text-gray-500">共 {total} 条记录</p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
              >
                上一页
              </button>
              <span className="text-sm text-gray-600">第 {page} / {totalPages} 页</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
