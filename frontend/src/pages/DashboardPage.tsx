import { useQuery } from '@tanstack/react-query'
import { FileCode, FolderTree, PlayCircle, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { casesApi, categoriesApi, tasksApi } from '@/lib/api'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: number | string
  icon: React.ElementType
  color: string
}

function StatCard({ title, value, icon: Icon, color }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={cn('p-3 rounded-lg', color)}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { data: casesData } = useQuery({
    queryKey: ['cases-stats'],
    queryFn: () => casesApi.list({ page: 1, page_size: 1 }),
  })

  const { data: categoriesData } = useQuery({
    queryKey: ['categories-stats'],
    queryFn: () => categoriesApi.list(),
  })

  const { data: tasksData } = useQuery({
    queryKey: ['tasks-stats'],
    queryFn: () => tasksApi.list({ page: 1, page_size: 10 }),
  })

  const totalCases = casesData?.data?.total || 0
  const totalCategories = categoriesData?.data?.total || 0
  const recentTasks = tasksData?.data?.items || []

  // Calculate task stats
  const completedTasks = recentTasks.filter((t: any) => t.status === 'completed').length
  const runningTasks = recentTasks.filter((t: any) => t.status === 'running').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>
        <p className="text-gray-500 mt-1">系统概览和统计信息</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="用例总数"
          value={totalCases}
          icon={FileCode}
          color="bg-blue-500"
        />
        <StatCard
          title="分类数量"
          value={totalCategories}
          icon={FolderTree}
          color="bg-purple-500"
        />
        <StatCard
          title="运行中任务"
          value={runningTasks}
          icon={PlayCircle}
          color="bg-green-500"
        />
        <StatCard
          title="已完成任务"
          value={completedTasks}
          icon={CheckCircle}
          color="bg-gray-500"
        />
      </div>

      {/* Recent Tasks */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">最近任务</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {recentTasks.length === 0 ? (
            <div className="p-6 text-center text-gray-500">暂无任务</div>
          ) : (
            recentTasks.slice(0, 5).map((task: any) => (
              <div key={task.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    'p-2 rounded-lg',
                    task.status === 'completed' ? 'bg-green-100' :
                    task.status === 'running' ? 'bg-blue-100' :
                    task.status === 'error' ? 'bg-red-100' : 'bg-gray-100'
                  )}>
                    {task.status === 'completed' ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : task.status === 'running' ? (
                      <PlayCircle className="h-5 w-5 text-blue-600" />
                    ) : task.status === 'error' ? (
                      <XCircle className="h-5 w-5 text-red-600" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-gray-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">任务 #{task.id}</p>
                    <p className="text-sm text-gray-500">目标: {task.target_ip}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {task.passed_count}/{task.total_cases} 通过
                  </p>
                  <p className="text-sm text-gray-500">{task.progress}%</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
