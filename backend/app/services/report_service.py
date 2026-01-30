"""
Report service for generating and exporting task reports.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.task import Task
from app.models.task_result import TaskResult
from app.models.case import Case
from app.models.category import Category
from app.models.user import User

logger = get_logger(__name__)


class ReportService:
    """Service class for generating task reports."""
    
    def __init__(self, db: Session):
        self.db = db
        self.reports_dir = Path(settings.REPORTS_DIR)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def get_task_report_data(self, task_id: int) -> Optional[dict]:
        """
        Get complete task data for report generation.
        
        Args:
            task_id: Task ID
            
        Returns:
            Dictionary with all report data
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        # Get user info
        user = self.db.query(User).filter(User.id == task.user_id).first()
        
        # Get results with case and category info
        results = (
            self.db.query(TaskResult)
            .filter(TaskResult.task_id == task_id)
            .order_by(TaskResult.id)
            .all()
        )
        
        result_details = []
        categories_summary = {}
        
        for r in results:
            case = self.db.query(Case).filter(Case.id == r.case_id).first()
            category = None
            if case:
                category = self.db.query(Category).filter(Category.id == case.category_id).first()
            
            category_name = category.name if category else "Unknown"
            
            # Update category summary
            if category_name not in categories_summary:
                categories_summary[category_name] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "error": 0,
                }
            categories_summary[category_name]["total"] += 1
            if r.status == "pass":
                categories_summary[category_name]["passed"] += 1
            elif r.status == "fail":
                categories_summary[category_name]["failed"] += 1
            else:
                categories_summary[category_name]["error"] += 1
            
            result_details.append({
                "id": r.id,
                "case_id": r.case_id,
                "case_name": case.name if case else "Unknown",
                "category": category_name,
                "risk_level": case.risk_level if case else "unknown",
                "description": case.description if case else None,
                "fix_suggestion": case.fix_suggestion if case else None,
                "status": r.status,
                "retry_count": r.retry_count,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "error_message": r.error_message,
            })
        
        # Calculate pass rate
        pass_rate = (task.passed_count / task.total_cases * 100) if task.total_cases > 0 else 0
        
        return {
            "task": {
                "id": task.id,
                "target_ip": task.target_ip,
                "description": task.description,
                "status": task.status,
                "total_cases": task.total_cases,
                "completed_cases": task.completed_cases,
                "passed_count": task.passed_count,
                "failed_count": task.failed_count,
                "error_count": task.error_count,
                "pass_rate": round(pass_rate, 1),
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "created_at": task.created_at.isoformat(),
            },
            "user": {
                "id": user.id if user else None,
                "username": user.username if user else "Unknown",
            },
            "categories_summary": categories_summary,
            "results": result_details,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def export_json(self, task_id: int) -> Optional[str]:
        """
        Export task report as JSON file.
        
        Args:
            task_id: Task ID
            
        Returns:
            Path to generated file or None
        """
        data = self.get_task_report_data(task_id)
        if not data:
            return None
        
        filename = f"report_task_{task_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON report generated: {filepath}")
        return str(filepath)
    
    def export_html(self, task_id: int) -> Optional[str]:
        """
        Export task report as HTML file.
        
        Args:
            task_id: Task ID
            
        Returns:
            Path to generated file or None
        """
        data = self.get_task_report_data(task_id)
        if not data:
            return None
        
        html_content = self._generate_html_report(data)
        
        filename = f"report_task_{task_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = self.reports_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {filepath}")
        return str(filepath)
    
    def _generate_html_report(self, data: dict) -> str:
        """Generate HTML report content."""
        task = data["task"]
        user = data["user"]
        categories = data["categories_summary"]
        results = data["results"]
        
        # Status color mapping
        status_colors = {
            "pass": "#28a745",
            "fail": "#dc3545",
            "error": "#ffc107",
            "pending": "#6c757d",
        }
        
        # Build results table rows
        results_rows = ""
        for r in results:
            status_color = status_colors.get(r["status"], "#6c757d")
            results_rows += f"""
            <tr>
                <td>{r['case_name']}</td>
                <td>{r['category']}</td>
                <td><span class="risk-{r['risk_level']}">{r['risk_level'].upper()}</span></td>
                <td><span style="color: {status_color}; font-weight: bold;">{r['status'].upper()}</span></td>
                <td>{r['error_message'] or '-'}</td>
            </tr>
            """
        
        # Build category summary rows
        category_rows = ""
        for cat_name, stats in categories.items():
            category_rows += f"""
            <tr>
                <td>{cat_name}</td>
                <td>{stats['total']}</td>
                <td style="color: #28a745;">{stats['passed']}</td>
                <td style="color: #dc3545;">{stats['failed']}</td>
                <td style="color: #ffc107;">{stats['error']}</td>
            </tr>
            """
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>安全检测报告 - Task #{task['id']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; min-width: 0; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #007bff; word-break: break-all; overflow-wrap: break-word; }}
        .summary-card .label {{ color: #666; margin-top: 5px; }}
        .summary-card .description {{ color: #888; font-size: 0.9em; margin-top: 8px; font-weight: normal; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        .risk-high {{ color: #dc3545; font-weight: bold; }}
        .risk-medium {{ color: #ffc107; font-weight: bold; }}
        .risk-low {{ color: #28a745; font-weight: bold; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 安全检测报告</h1>
        
        <div class="summary">
            <div class="summary-card">
                <div class="value">{task['target_ip']}</div>
                <div class="label">目标 IP</div>
                {f'<div class="description">{task["description"]}</div>' if task.get('description') else ''}
            </div>
            <div class="summary-card">
                <div class="value">{task['total_cases']}</div>
                <div class="label">总用例数</div>
            </div>
            <div class="summary-card">
                <div class="value" style="color: #28a745;">{task['passed_count']}</div>
                <div class="label">通过</div>
            </div>
            <div class="summary-card">
                <div class="value" style="color: #dc3545;">{task['failed_count']}</div>
                <div class="label">失败</div>
            </div>
            <div class="summary-card">
                <div class="value">{task['pass_rate']}%</div>
                <div class="label">通过率</div>
            </div>
        </div>
        
        <h2>📊 分类统计</h2>
        <table>
            <thead>
                <tr>
                    <th>分类</th>
                    <th>总数</th>
                    <th>通过</th>
                    <th>失败</th>
                    <th>错误</th>
                </tr>
            </thead>
            <tbody>
                {category_rows}
            </tbody>
        </table>
        
        <h2>📋 详细结果</h2>
        <table>
            <thead>
                <tr>
                    <th>用例名称</th>
                    <th>分类</th>
                    <th>风险等级</th>
                    <th>状态</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
                {results_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p>任务 ID: {task['id']} | 执行人: {user['username']} | 开始时间: {task['start_time'] or 'N/A'} | 结束时间: {task['end_time'] or 'N/A'}</p>
            <p>报告生成时间: {data['generated_at']}</p>
        </div>
    </div>
</body>
</html>
        """
        return html
