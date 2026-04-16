"""
DataQ 告警通知模块
支持邮件、企业微信、钉钉等多种通知渠道
"""
import smtplib
import requests
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)


class AlertChannel:
    """告警渠道基类"""
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """发送告警"""
        raise NotImplementedError


class EmailAlert(AlertChannel):
    """邮件告警"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, from_addr: str, to_addrs: List[str]):
        """
        初始化邮件告警
        
        Args:
            smtp_server: SMTP 服务器地址
            smtp_port: SMTP 端口
            username: 用户名
            password: 密码/授权码
            from_addr: 发件人地址
            to_addrs: 收件人列表
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """发送邮件告警"""
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            msg['Subject'] = f"[DataQ] {title}"
            
            # 添加纯文本内容
            text_part = MIMEText(message, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # 添加 HTML 内容（可选）
            html_content = kwargs.get('html_content')
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 发送邮件
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.ehlo()
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.from_addr, self.to_addrs, msg.as_string())
            server.quit()
            
            logger.info(f"邮件告警发送成功: {title}")
            return True
            
        except Exception as e:
            logger.error(f"邮件告警发送失败: {e}")
            return False


class WeComAlert(AlertChannel):
    """企业微信告警"""
    
    def __init__(self, webhook_url: str):
        """
        初始化企业微信告警
        
        Args:
            webhook_url: 企业微信机器人 Webhook URL
        """
        self.webhook_url = webhook_url
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """发送企业微信告警"""
        try:
            # 构建消息
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"## {title}\n\n{message}"
                }
            }
            
            # 发送请求
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            result = response.json()
            if result.get('errcode') == 0:
                logger.info(f"企业微信告警发送成功: {title}")
                return True
            else:
                logger.error(f"企业微信告警发送失败: {result.get('errmsg')}")
                return False
                
        except Exception as e:
            logger.error(f"企业微信告警发送异常: {e}")
            return False


class DingTalkAlert(AlertChannel):
    """钉钉告警"""
    
    def __init__(self, webhook_url: str, secret: str = None):
        """
        初始化钉钉告警
        
        Args:
            webhook_url: 钉钉机器人 Webhook URL
            secret: 加签密钥（可选）
        """
        self.webhook_url = webhook_url
        self.secret = secret
    
    def send(self, title: str, message: str, **kwargs) -> bool:
        """发送钉钉告警"""
        try:
            # 构建消息
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"[DataQ] {title}",
                    "text": f"## {title}\n\n{message}"
                }
            }
            
            # 如果有密钥，添加签名
            if self.secret:
                import hmac
                import hashlib
                import base64
                import time
                
                timestamp = str(round(time.time() * 1000))
                secret_enc = self.secret.encode('utf-8')
                string_to_sign = f'{timestamp}\n{self.secret}'
                string_to_sign_enc = string_to_sign.encode('utf-8')
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = base64.b64encode(hmac_code).decode('utf-8')
                
                payload['timestamp'] = timestamp
                payload['sign'] = sign
            
            # 发送请求
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            result = response.json()
            if result.get('errcode') == 0:
                logger.info(f"钉钉告警发送成功: {title}")
                return True
            else:
                logger.error(f"钉钉告警发送失败: {result.get('errmsg')}")
                return False
                
        except Exception as e:
            logger.error(f"钉钉告警发送异常: {e}")
            return False


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        """初始化告警管理器"""
        self.channels: Dict[str, AlertChannel] = {}
    
    def add_channel(self, channel_name: str, channel: AlertChannel):
        """添加告警渠道"""
        self.channels[channel_name] = channel
        logger.info(f"已添加告警渠道: {channel_name}")
    
    def remove_channel(self, channel_name: str):
        """移除告警渠道"""
        if channel_name in self.channels:
            del self.channels[channel_name]
            logger.info(f"已移除告警渠道: {channel_name}")
    
    def send_alert(self, channel_names: List[str], title: str, message: str, **kwargs):
        """
        发送告警到指定渠道
        
        Args:
            channel_names: 渠道名称列表
            title: 告警标题
            message: 告警内容
            **kwargs: 额外参数
        """
        results = {}
        
        for channel_name in channel_names:
            if channel_name in self.channels:
                success = self.channels[channel_name].send(title, message, **kwargs)
                results[channel_name] = success
            else:
                logger.warning(f"告警渠道不存在: {channel_name}")
                results[channel_name] = False
        
        return results
    
    def send_all(self, title: str, message: str, **kwargs):
        """发送到所有已配置的渠道"""
        return self.send_alert(list(self.channels.keys()), title, message, **kwargs)


# 全局告警管理器实例
alert_manager = AlertManager()


def init_default_alerts(config: dict = None):
    """
    初始化默认告警配置
    
    Args:
        config: 告警配置字典
    """
    if not config:
        logger.info("未配置告警渠道，跳过初始化")
        return
    
    # 配置邮件告警
    if 'email' in config:
        email_config = config['email']
        email_alert = EmailAlert(
            smtp_server=email_config['smtp_server'],
            smtp_port=email_config.get('smtp_port', 587),
            username=email_config['username'],
            password=email_config['password'],
            from_addr=email_config['from_addr'],
            to_addrs=email_config['to_addrs']
        )
        alert_manager.add_channel('email', email_alert)
    
    # 配置企业微信告警
    if 'wecom' in config:
        wecom_config = config['wecom']
        wecom_alert = WeComAlert(webhook_url=wecom_config['webhook_url'])
        alert_manager.add_channel('wecom', wecom_alert)
    
    # 配置钉钉告警
    if 'dingtalk' in config:
        dingtalk_config = config['dingtalk']
        dingtalk_alert = DingTalkAlert(
            webhook_url=dingtalk_config['webhook_url'],
            secret=dingtalk_config.get('secret')
        )
        alert_manager.add_channel('dingtalk', dingtalk_alert)
    
    logger.info(f"告警渠道初始化完成: {list(alert_manager.channels.keys())}")


def format_validation_failure_alert(asset_name: str, failed_rules: list, 
                                   validation_result: dict) -> tuple:
    """
    格式化校验失败告警
    
    Args:
        asset_name: 资产名称
        failed_rules: 失败的规则列表
        validation_result: 校验结果
    
    Returns:
        (title, message) 元组
    """
    title = f"数据质量校验失败: {asset_name}"
    
    message = f"**资产名称**: {asset_name}\n\n"
    message += f"**校验时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    message += f"**失败规则数**: {len(failed_rules)}\n\n"
    message += "**失败详情**:\n\n"
    
    for i, rule in enumerate(failed_rules, 1):
        message += f"{i}. **{rule.get('rule_name', '未知规则')}**\n"
        message += f"   - 规则类型: {rule.get('rule_type', 'N/A')}\n"
        message += f"   - 字段: {rule.get('column_name', 'N/A')}\n"
        message += f"   - 成功率: {rule.get('success_percent', 0):.2f}%\n\n"
    
    message += "---\n"
    message += "请及时处理数据质量问题！"
    
    return title, message
