"""
DataQ 定时任务调度器
基于 APScheduler 实现自动质量校验调度
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import json
import logging

from db_utils import get_session, AssetManager, RuleManager, ValidationHistoryManager
from quality_runner import QualityRunner, StrongRuleFailedException

# 导入告警模块（可选）
try:
    from alert_notifier import alert_manager, format_validation_failure_alert
    ALERT_ENABLED = True
except ImportError:
    ALERT_ENABLED = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler = BackgroundScheduler()
        self.scheduled_jobs = {}  # 存储已调度的任务 {asset_id: job_id}
        
    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("任务调度器已启动")
            
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("任务调度器已关闭")
            
    def add_asset_validation_job(self, asset_id: int, schedule_type: str = 'interval',
                                 interval_hours: int = 24, cron_expression: str = None,
                                 rule_ids: list = None, auto_archive: bool = True,
                                 auto_create_issue: bool = True):
        """
        为资产添加定时校验任务
        
        Args:
            asset_id: 资产ID
            schedule_type: 调度类型 ('interval' 或 'cron')
            interval_hours: 间隔小时数（当 schedule_type='interval'）
            cron_expression: Cron 表达式（当 schedule_type='cron'），如 "0 9 * * *" (每天9点)
            rule_ids: 指定规则ID列表，None表示执行所有激活规则
            auto_archive: 是否自动归档异常数据
            auto_create_issue: 是否自动创建问题工单
        """
        session = get_session()
        try:
            # 验证资产是否存在
            asset = AssetManager.get_asset(session, asset_id)
            if not asset:
                raise ValueError(f"资产不存在: asset_id={asset_id}")
            
            # 移除已存在的任务
            if asset_id in self.scheduled_jobs:
                self.remove_job(asset_id)
            
            # 定义任务函数
            def job_func():
                self._execute_scheduled_validation(
                    asset_id=asset_id,
                    rule_ids=rule_ids,
                    auto_archive=auto_archive,
                    auto_create_issue=auto_create_issue
                )
            
            # 添加任务到调度器
            if schedule_type == 'interval':
                trigger = IntervalTrigger(hours=interval_hours)
                job = self.scheduler.add_job(
                    func=job_func,
                    trigger=trigger,
                    id=f'asset_{asset_id}_validation',
                    name=f'资产校验: {asset.name}',
                    replace_existing=True
                )
            elif schedule_type == 'cron':
                if not cron_expression:
                    raise ValueError("Cron 调度需要 cron_expression 参数")
                
                # 解析 cron 表达式 (分 时 日 月 周)
                parts = cron_expression.split()
                if len(parts) != 5:
                    raise ValueError("Cron 表达式格式错误，应为: 分 时 日 月 周")
                
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
                job = self.scheduler.add_job(
                    func=job_func,
                    trigger=trigger,
                    id=f'asset_{asset_id}_validation',
                    name=f'资产校验: {asset.name}',
                    replace_existing=True
                )
            else:
                raise ValueError(f"不支持的调度类型: {schedule_type}")
            
            # 记录任务
            self.scheduled_jobs[asset_id] = job.id
            
            logger.info(f"已添加定时任务: asset_id={asset_id}, schedule_type={schedule_type}, job_id={job.id}")
            
            return job.id
            
        except Exception as e:
            logger.error(f"添加定时任务失败: {e}")
            raise
        finally:
            session.close()
    
    def remove_job(self, asset_id: int):
        """移除资产的定时校验任务"""
        if asset_id in self.scheduled_jobs:
            job_id = self.scheduled_jobs[asset_id]
            try:
                self.scheduler.remove_job(job_id)
                del self.scheduled_jobs[asset_id]
                logger.info(f"已移除定时任务: asset_id={asset_id}, job_id={job_id}")
            except Exception as e:
                logger.error(f"移除定时任务失败: {e}")
    
    def get_job_status(self, asset_id: int):
        """获取任务的调度状态"""
        if asset_id in self.scheduled_jobs:
            job_id = self.scheduled_jobs[asset_id]
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    'asset_id': asset_id,
                    'job_id': job_id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'status': 'scheduled'
                }
        return {
            'asset_id': asset_id,
            'status': 'not_scheduled'
        }
    
    def list_all_jobs(self):
        """列出所有已调度的任务"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'job_id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            })
        return jobs
    
    def _execute_scheduled_validation(self, asset_id: int, rule_ids: list = None,
                                     auto_archive: bool = True, auto_create_issue: bool = True):
        """
        执行定时校验任务
        
        Args:
            asset_id: 资产ID
            rule_ids: 规则ID列表
            auto_archive: 是否自动归档
            auto_create_issue: 是否自动创建问题工单
        """
        logger.info(f"开始执行定时校验: asset_id={asset_id}")
        
        session = get_session()
        try:
            runner = QualityRunner(session=session)
            
            result = runner.run_asset_validation(
                asset_id=asset_id,
                rule_ids=rule_ids,
                auto_archive=auto_archive,
                auto_create_issue=auto_create_issue
            )
            
            logger.info(f"定时校验完成: asset_id={asset_id}, success={result['success']}")
            
            # 如果校验失败且有强规则失败，发送告警
            if not result['success']:
                self._send_alert_on_failure(asset_id, result)
            
            return result
            
        except StrongRuleFailedException as e:
            logger.error(f"强规则失败: asset_id={asset_id}, error={str(e)}")
            self._send_alert_on_failure(asset_id, {'error': str(e), 'failed_rules': e.failed_rules})
            raise
        except Exception as e:
            logger.error(f"定时校验异常: asset_id={asset_id}, error={str(e)}")
            raise
        finally:
            session.close()
    
    def _send_alert_on_failure(self, asset_id: int, result: dict):
        """校验失败时发送告警"""
        if not ALERT_ENABLED or not alert_manager.channels:
            logger.warning(f"告警未启用或没有配置渠道，跳过告警")
            return
        
        try:
            session = get_session()
            try:
                asset = AssetManager.get_asset(session, asset_id)
                if not asset:
                    logger.error(f"资产不存在: asset_id={asset_id}")
                    return
                
                # 构建失败规则列表
                failed_rules = []
                if 'failed_rules' in result:
                    failed_rules = result['failed_rules']
                elif isinstance(result, dict) and 'results' in result:
                    for r in result['results']:
                        if not r.get('success', True):
                            failed_rules.append({
                                'rule_name': r.get('rule_name', 'Unknown'),
                                'rule_type': r.get('rule_type', 'N/A'),
                                'column_name': r.get('column_name', 'N/A'),
                                'success_percent': r.get('pass_rate', 0)
                            })
                
                # 格式化告警消息
                title, message = format_validation_failure_alert(
                    asset_name=asset.name,
                    failed_rules=failed_rules,
                    validation_result=result
                )
                
                # 发送告警
                alert_manager.send_all(title, message)
                logger.info(f"已发送告警通知: asset_id={asset_id}")
                
            finally:
                session.close()
        except Exception as e:
            logger.error(f"发送告警失败: {e}")


# 全局调度器实例
scheduler = TaskScheduler()


def init_scheduler():
    """初始化并启动调度器"""
    scheduler.start()
    logger.info("调度器初始化完成")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown()
    logger.info("调度器已关闭")
