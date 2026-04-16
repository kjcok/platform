"""
测试第四阶段：自动化与集成
包括定时任务、告警通知、数据库连接器、JWT 认证
"""
import unittest
import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_path = os.path.join(project_root, 'src', 'backend')
sys.path.insert(0, backend_path)


class TestScheduler(unittest.TestCase):
    """测试定时任务调度器"""
    
    def setUp(self):
        """设置测试环境"""
        from scheduler import TaskScheduler
        self.scheduler = TaskScheduler()
        
        # 创建测试资产
        from db_utils import get_session, AssetManager
        self.session = get_session()
        self.asset = AssetManager.create_asset(
            session=self.session,
            name='测试调度资产',
            data_source='test_schedule.csv',
            asset_type='csv',
            owner='测试用户'
        )
        self.session.commit()
    
    def tearDown(self):
        """清理测试环境"""
        # 关闭调度器
        if hasattr(self, 'scheduler') and self.scheduler.scheduler.running:
            self.scheduler.shutdown()
        
        # 删除测试资产
        if hasattr(self, 'asset'):
            from db_utils import AssetManager
            AssetManager.delete_asset(self.session, self.asset.id)
            self.session.commit()
        
        if hasattr(self, 'session'):
            self.session.close()
    
    def test_scheduler_start_stop(self):
        """测试调度器启动和停止"""
        self.assertFalse(self.scheduler.scheduler.running)
        self.scheduler.start()
        self.assertTrue(self.scheduler.scheduler.running)
        self.scheduler.shutdown()
        self.assertFalse(self.scheduler.scheduler.running)
    
    def test_add_interval_job(self):
        """测试添加间隔调度任务"""
        self.scheduler.start()
        
        job_id = self.scheduler.add_asset_validation_job(
            asset_id=self.asset.id,
            schedule_type='interval',
            interval_hours=24
        )
        
        self.assertIsNotNone(job_id)
        self.assertIn(self.asset.id, self.scheduler.scheduled_jobs)
        
        # 检查任务状态
        status = self.scheduler.get_job_status(self.asset.id)
        self.assertEqual(status['status'], 'scheduled')
        self.assertIsNotNone(status['next_run_time'])
    
    def test_add_cron_job(self):
        """测试添加 Cron 调度任务"""
        self.scheduler.start()
        
        job_id = self.scheduler.add_asset_validation_job(
            asset_id=self.asset.id,
            schedule_type='cron',
            cron_expression='0 9 * * *'  # 每天 9 点
        )
        
        self.assertIsNotNone(job_id)
        self.assertIn(self.asset.id, self.scheduler.scheduled_jobs)
    
    def test_remove_job(self):
        """测试移除任务"""
        self.scheduler.start()
        
        # 添加任务
        self.scheduler.add_asset_validation_job(
            asset_id=self.asset.id,
            schedule_type='interval',
            interval_hours=24
        )
        
        # 移除任务
        self.scheduler.remove_job(self.asset.id)
        
        self.assertNotIn(self.asset.id, self.scheduler.scheduled_jobs)
        status = self.scheduler.get_job_status(self.asset.id)
        self.assertEqual(status['status'], 'not_scheduled')
    
    def test_list_all_jobs(self):
        """测试列出所有任务"""
        self.scheduler.start()
        
        from db_utils import AssetManager
        
        # 添加多个任务
        asset2 = AssetManager.create_asset(
            session=self.session,
            name='测试资产2',
            data_source='test2.csv',
            asset_type='csv'
        )
        self.session.commit()
        
        self.scheduler.add_asset_validation_job(
            asset_id=self.asset.id,
            schedule_type='interval',
            interval_hours=24
        )
        self.scheduler.add_asset_validation_job(
            asset_id=asset2.id,
            schedule_type='interval',
            interval_hours=12
        )
        
        jobs = self.scheduler.list_all_jobs()
        self.assertEqual(len(jobs), 2)
        
        # 清理
        AssetManager.delete_asset(self.session, asset2.id)
        self.session.commit()


class TestAlertNotifier(unittest.TestCase):
    """测试告警通知模块"""
    
    def test_email_alert_creation(self):
        """测试邮件告警对象创建"""
        try:
            from alert_notifier import EmailAlert
            alert = EmailAlert(
                smtp_server='smtp.test.com',
                smtp_port=587,
                username='test@test.com',
                password='password',
                from_addr='test@test.com',
                to_addrs=['recipient@test.com']
            )
            self.assertIsNotNone(alert)
            self.assertEqual(alert.smtp_server, 'smtp.test.com')
        except ImportError:
            self.skipTest("告警模块未安装")
    
    def test_wecom_alert_creation(self):
        """测试企业微信告警对象创建"""
        try:
            from alert_notifier import WeComAlert
            alert = WeComAlert(webhook_url='https://qyapi.weixin.qq.com/test')
            self.assertIsNotNone(alert)
            self.assertEqual(alert.webhook_url, 'https://qyapi.weixin.qq.com/test')
        except ImportError:
            self.skipTest("告警模块未安装")
    
    def test_dingtalk_alert_creation(self):
        """测试钉钉告警对象创建"""
        try:
            from alert_notifier import DingTalkAlert
            alert = DingTalkAlert(
                webhook_url='https://oapi.dingtalk.com/test',
                secret='test_secret'
            )
            self.assertIsNotNone(alert)
            self.assertEqual(alert.webhook_url, 'https://oapi.dingtalk.com/test')
        except ImportError:
            self.skipTest("告警模块未安装")
    
    def test_alert_manager(self):
        """测试告警管理器"""
        try:
            from alert_notifier import AlertManager, EmailAlert
            
            manager = AlertManager()
            
            # 添加渠道
            email_alert = EmailAlert(
                smtp_server='smtp.test.com',
                smtp_port=587,
                username='test@test.com',
                password='password',
                from_addr='test@test.com',
                to_addrs=['recipient@test.com']
            )
            manager.add_channel('email', email_alert)
            
            self.assertIn('email', manager.channels)
            
            # 移除渠道
            manager.remove_channel('email')
            self.assertNotIn('email', manager.channels)
        except ImportError:
            self.skipTest("告警模块未安装")
    
    def test_format_failure_alert(self):
        """测试格式化校验失败告警"""
        try:
            from alert_notifier import format_validation_failure_alert
            
            title, message = format_validation_failure_alert(
                asset_name='测试资产',
                failed_rules=[
                    {
                        'rule_name': '邮箱唯一性',
                        'rule_type': 'uniqueness',
                        'column_name': 'email',
                        'success_percent': 85.5
                    }
                ],
                validation_result={'success': False}
            )
            
            self.assertIn('测试资产', title)
            self.assertIn('邮箱唯一性', message)
            self.assertIn('85.50%', message)
        except ImportError:
            self.skipTest("告警模块未安装")


class TestDatabaseConnector(unittest.TestCase):
    """测试数据库连接器"""
    
    def test_mysql_connector_creation(self):
        """测试 MySQL 连接器创建"""
        try:
            from db_connector import MySQLConnector
            
            connector = MySQLConnector(
                host='localhost',
                port=3306,
                database='test_db',
                username='root',
                password='password'
            )
            
            self.assertIsNotNone(connector)
            self.assertIn('mysql+pymysql', connector.connection_string)
            self.assertEqual(connector.get_db_type(), 'MySQL')
        except ImportError:
            self.skipTest("数据库连接器模块未安装")
    
    def test_postgresql_connector_creation(self):
        """测试 PostgreSQL 连接器创建"""
        try:
            from db_connector import PostgreSQLConnector
            
            connector = PostgreSQLConnector(
                host='localhost',
                port=5432,
                database='test_db',
                username='postgres',
                password='password'
            )
            
            self.assertIsNotNone(connector)
            self.assertIn('postgresql', connector.connection_string)
            self.assertEqual(connector.get_db_type(), 'PostgreSQL')
        except ImportError:
            self.skipTest("数据库连接器模块未安装")
    
    def test_sqlserver_connector_creation(self):
        """测试 SQL Server 连接器创建"""
        try:
            from db_connector import SQLServerConnector
            
            connector = SQLServerConnector(
                host='localhost',
                port=1433,
                database='test_db',
                username='sa',
                password='password'
            )
            
            self.assertIsNotNone(connector)
            self.assertIn('mssql+pyodbc', connector.connection_string)
            self.assertEqual(connector.get_db_type(), 'SQL Server')
        except ImportError:
            self.skipTest("数据库连接器模块未安装")
    
    def test_create_connector_factory(self):
        """测试连接器工厂函数"""
        try:
            from db_connector import create_connector
            
            # 测试 MySQL
            mysql_conn = create_connector('mysql', host='localhost', username='root', password='pwd')
            self.assertIsInstance(mysql_conn, object)
            
            # 测试 PostgreSQL
            pg_conn = create_connector('postgresql', host='localhost', username='postgres', password='pwd')
            self.assertIsInstance(pg_conn, object)
            
            # 测试不支持的类型
            with self.assertRaises(ValueError):
                create_connector('unsupported_db', host='localhost')
        except ImportError:
            self.skipTest("数据库连接器模块未安装")


class TestJWTAuth(unittest.TestCase):
    """测试 JWT 认证"""
    
    def setUp(self):
        """设置测试环境"""
        try:
            from auth import JWTAuth
            # 使用更长的密钥（至少32字节）以避免警告
            self.jwt_auth = JWTAuth(
                secret_key='test-secret-key-for-jwt-auth-32bytes!',
                token_expiry_hours=1
            )
        except ImportError:
            self.skipTest("认证模块未安装")
    
    def test_generate_token(self):
        """测试生成 Token"""
        token = self.jwt_auth.generate_token(
            user_id='1',
            username='testuser',
            role='admin'
        )
        
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
    
    def test_verify_token(self):
        """测试验证 Token"""
        token = self.jwt_auth.generate_token(
            user_id='1',
            username='testuser',
            role='user'
        )
        
        payload = self.jwt_auth.verify_token(token)
        
        self.assertEqual(payload['user_id'], '1')
        self.assertEqual(payload['username'], 'testuser')
        self.assertEqual(payload['role'], 'user')
    
    def test_expired_token(self):
        """测试过期 Token"""
        import jwt
        
        # 创建一个已过期的 Token
        import datetime
        now = datetime.datetime.utcnow()
        payload = {
            'user_id': '1',
            'username': 'testuser',
            'exp': now - datetime.timedelta(hours=1),  # 已过期
            'iat': now - datetime.timedelta(hours=2)
        }
        expired_token = jwt.encode(payload, self.jwt_auth.secret_key, algorithm='HS256')
        
        with self.assertRaises(jwt.ExpiredSignatureError):
            self.jwt_auth.verify_token(expired_token)
    
    def test_invalid_token(self):
        """测试无效 Token"""
        import jwt
        
        with self.assertRaises(jwt.InvalidTokenError):
            self.jwt_auth.verify_token('invalid.token.here')
    
    def test_refresh_token(self):
        """测试刷新 Token"""
        old_token = self.jwt_auth.generate_token(
            user_id='1',
            username='testuser',
            role='user'
        )
        
        # 等待一小段时间，确保时间戳不同
        time.sleep(0.1)
        
        new_token = self.jwt_auth.refresh_token(old_token)
        
        self.assertIsNotNone(new_token)
        
        # 验证新 Token 有效
        payload = self.jwt_auth.verify_token(new_token)
        self.assertEqual(payload['username'], 'testuser')


if __name__ == '__main__':
    unittest.main()
