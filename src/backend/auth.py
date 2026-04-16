"""
DataQ JWT 认证模块
提供基于 Token 的 API 认证和授权
"""
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, g
import logging

logger = logging.getLogger(__name__)


class JWTAuth:
    """JWT 认证器"""
    
    def __init__(self, secret_key: str = None, token_expiry_hours: int = 24):
        """
        初始化 JWT 认证器
        
        Args:
            secret_key: JWT 密钥（建议使用环境变量）
            token_expiry_hours: Token 过期时间（小时）
        """
        self.secret_key = secret_key or 'dataq-secret-key-change-in-production'
        self.token_expiry_hours = token_expiry_hours
    
    def generate_token(self, user_id: str, username: str, role: str = 'user', 
                      extra_data: dict = None) -> str:
        """
        生成 JWT Token
        
        Args:
            user_id: 用户ID
            username: 用户名
            role: 用户角色 ('admin', 'user', 'viewer')
            extra_data: 额外数据
        
        Returns:
            JWT Token 字符串
        """
        now = datetime.datetime.utcnow()
        
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'iat': now,  # Issued At
            'exp': now + datetime.timedelta(hours=self.token_expiry_hours),  # Expiration
            'nbf': now  # Not Before
        }
        
        if extra_data:
            payload.update(extra_data)
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        logger.info(f"Token 生成成功: user={username}, role={role}")
        
        return token
    
    def verify_token(self, token: str) -> dict:
        """
        验证 JWT Token
        
        Args:
            token: JWT Token 字符串
        
        Returns:
            解码后的 payload 字典
        
        Raises:
            jwt.ExpiredSignatureError: Token 已过期
            jwt.InvalidTokenError: Token 无效
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            logger.debug(f"Token 验证成功: user={payload.get('username')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token 已过期")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token 无效: {e}")
            raise
    
    def refresh_token(self, old_token: str) -> str:
        """
        刷新 Token（生成新的 Token）
        
        Args:
            old_token: 旧的 Token
        
        Returns:
            新的 Token
        """
        try:
            payload = self.verify_token(old_token)
            
            # 使用旧 payload 中的信息生成新 Token
            new_token = self.generate_token(
                user_id=payload['user_id'],
                username=payload['username'],
                role=payload.get('role', 'user'),
                extra_data={k: v for k, v in payload.items() 
                           if k not in ['user_id', 'username', 'role', 'iat', 'exp', 'nbf']}
            )
            
            logger.info(f"Token 刷新成功: user={payload['username']}")
            return new_token
            
        except Exception as e:
            logger.error(f"Token 刷新失败: {e}")
            raise


# 全局 JWT 认证器实例
jwt_auth = JWTAuth()


def token_required(f):
    """
    Token 验证装饰器
    
    用法:
        @app.route('/api/protected')
        @token_required
        def protected_route():
            current_user = g.current_user
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取 Token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # 支持 "Bearer <token>" 格式
                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == 'bearer':
                    token = parts[1]
                else:
                    token = auth_header
            except Exception:
                token = None
        
        if not token:
            return jsonify({
                'status': 'error',
                'message': '缺少认证 Token'
            }), 401
        
        try:
            # 验证 Token
            payload = jwt_auth.verify_token(token)
            g.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({
                'status': 'error',
                'message': 'Token 已过期，请重新登录'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'status': 'error',
                'message': '无效的 Token'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """
    管理员权限验证装饰器
    
    用法:
        @app.route('/api/admin')
        @token_required
        @admin_required
        def admin_route():
            ...
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user.get('role') != 'admin':
            return jsonify({
                'status': 'error',
                'message': '需要管理员权限'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated


def role_required(required_role: str):
    """
    角色权限验证装饰器
    
    用法:
        @app.route('/api/editor')
        @token_required
        @role_required('editor')
        def editor_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            user_role = g.current_user.get('role', 'user')
            
            # 角色优先级: admin > editor > user > viewer
            role_hierarchy = {
                'admin': 4,
                'editor': 3,
                'user': 2,
                'viewer': 1
            }
            
            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(required_role, 0)
            
            if user_level < required_level:
                return jsonify({
                    'status': 'error',
                    'message': f'需要 {required_role} 或更高权限'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def init_jwt_auth(secret_key: str = None, token_expiry_hours: int = 24):
    """
    初始化 JWT 认证
    
    Args:
        secret_key: JWT 密钥
        token_expiry_hours: Token 过期时间（小时）
    """
    global jwt_auth
    jwt_auth = JWTAuth(secret_key=secret_key, token_expiry_hours=token_expiry_hours)
    logger.info(f"JWT 认证初始化完成, token_expiry={token_expiry_hours}h")
