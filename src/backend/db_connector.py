"""
DataQ 数据源连接器
支持多种数据库直连：MySQL、PostgreSQL、SQLite、SQL Server 等
"""
import pandas as pd
from sqlalchemy import create_engine
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """数据库连接器基类"""
    
    def __init__(self, connection_string: str):
        """
        初始化数据库连接器
        
        Args:
            connection_string: 数据库连接字符串
        """
        self.connection_string = connection_string
        self.engine = None
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.engine = create_engine(self.connection_string)
            logger.info(f"数据库连接成功: {self.get_db_type()}")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已断开")
    
    def get_db_type(self) -> str:
        """获取数据库类型"""
        raise NotImplementedError
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        执行查询并返回 DataFrame
        
        Args:
            query: SQL 查询语句
        
        Returns:
            Pandas DataFrame
        """
        if not self.engine:
            raise Exception("数据库未连接，请先调用 connect()")
        
        try:
            df = pd.read_sql_query(query, self.engine)
            logger.info(f"查询执行成功，返回 {len(df)} 行数据")
            return df
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> Dict:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
        
        Returns:
            表结构信息字典
        """
        raise NotImplementedError
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


class MySQLConnector(DatabaseConnector):
    """MySQL 数据库连接器"""
    
    def __init__(self, host: str, port: int = 3306, database: str = None,
                 username: str = None, password: str = None, **kwargs):
        """
        初始化 MySQL 连接器
        
        Args:
            host: 主机地址
            port: 端口号
            database: 数据库名
            username: 用户名
            password: 密码
            **kwargs: 其他参数（如 charset, pool_size 等）
        """
        # 构建连接字符串
        connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}"
        if database:
            connection_string += f"/{database}"
        
        # 添加额外参数
        if kwargs:
            params = '&'.join([f"{k}={v}" for k, v in kwargs.items()])
            connection_string += f"?{params}"
        
        super().__init__(connection_string)
    
    def get_db_type(self) -> str:
        return "MySQL"
    
    def get_table_info(self, table_name: str) -> Dict:
        """获取 MySQL 表结构"""
        query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_KEY,
                COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """
        df = self.execute_query(query)
        
        return {
            'table_name': table_name,
            'columns': df.to_dict('records'),
            'row_count': len(df)
        }


class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL 数据库连接器"""
    
    def __init__(self, host: str, port: int = 5432, database: str = None,
                 username: str = None, password: str = None, **kwargs):
        """
        初始化 PostgreSQL 连接器
        
        Args:
            host: 主机地址
            port: 端口号
            database: 数据库名
            username: 用户名
            password: 密码
            **kwargs: 其他参数
        """
        connection_string = f"postgresql://{username}:{password}@{host}:{port}"
        if database:
            connection_string += f"/{database}"
        
        if kwargs:
            params = '&'.join([f"{k}={v}" for k, v in kwargs.items()])
            connection_string += f"?{params}"
        
        super().__init__(connection_string)
    
    def get_db_type(self) -> str:
        return "PostgreSQL"
    
    def get_table_info(self, table_name: str) -> Dict:
        """获取 PostgreSQL 表结构"""
        query = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """
        df = self.execute_query(query)
        
        return {
            'table_name': table_name,
            'columns': df.to_dict('records'),
            'row_count': len(df)
        }


class SQLServerConnector(DatabaseConnector):
    """SQL Server 数据库连接器"""
    
    def __init__(self, host: str, port: int = 1433, database: str = None,
                 username: str = None, password: str = None, **kwargs):
        """
        初始化 SQL Server 连接器
        
        Args:
            host: 主机地址
            port: 端口号
            database: 数据库名
            username: 用户名
            password: 密码
            **kwargs: 其他参数
        """
        connection_string = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        
        if kwargs:
            params = '&'.join([f"{k}={v}" for k, v in kwargs.items()])
            connection_string += f"&{params}"
        
        super().__init__(connection_string)
    
    def get_db_type(self) -> str:
        return "SQL Server"
    
    def get_table_info(self, table_name: str) -> Dict:
        """获取 SQL Server 表结构"""
        query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """
        df = self.execute_query(query)
        
        return {
            'table_name': table_name,
            'columns': df.to_dict('records'),
            'row_count': len(df)
        }


class OracleConnector(DatabaseConnector):
    """Oracle 数据库连接器"""
    
    def __init__(self, host: str, port: int = 1521, service_name: str = None,
                 username: str = None, password: str = None, **kwargs):
        """
        初始化 Oracle 连接器
        
        Args:
            host: 主机地址
            port: 端口号
            service_name: 服务名
            username: 用户名
            password: 密码
            **kwargs: 其他参数
        """
        connection_string = f"oracle+cx_oracle://{username}:{password}@{host}:{port}/?service_name={service_name}"
        
        if kwargs:
            params = '&'.join([f"{k}={v}" for k, v in kwargs.items()])
            connection_string += f"&{params}"
        
        super().__init__(connection_string)
    
    def get_db_type(self) -> str:
        return "Oracle"
    
    def get_table_info(self, table_name: str) -> Dict:
        """获取 Oracle 表结构"""
        query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                NULLABLE,
                DATA_DEFAULT
            FROM ALL_TAB_COLUMNS
            WHERE TABLE_NAME = UPPER('{table_name}')
            ORDER BY COLUMN_ID
        """
        df = self.execute_query(query)
        
        return {
            'table_name': table_name,
            'columns': df.to_dict('records'),
            'row_count': len(df)
        }


def create_connector(db_type: str, **kwargs) -> DatabaseConnector:
    """
    工厂函数：创建数据库连接器
    
    Args:
        db_type: 数据库类型 ('mysql', 'postgresql', 'sqlserver', 'oracle')
        **kwargs: 连接参数
    
    Returns:
        DatabaseConnector 实例
    """
    connectors = {
        'mysql': MySQLConnector,
        'postgresql': PostgreSQLConnector,
        'postgres': PostgreSQLConnector,
        'sqlserver': SQLServerConnector,
        'mssql': SQLServerConnector,
        'oracle': OracleConnector
    }
    
    connector_class = connectors.get(db_type.lower())
    if not connector_class:
        raise ValueError(f"不支持的数据库类型: {db_type}。支持的类型: {list(connectors.keys())}")
    
    return connector_class(**kwargs)


def load_data_from_database(db_type: str, query: str, **connection_params) -> pd.DataFrame:
    """
    便捷函数：从数据库加载数据
    
    Args:
        db_type: 数据库类型
        query: SQL 查询语句
        **connection_params: 连接参数
    
    Returns:
        Pandas DataFrame
    """
    connector = create_connector(db_type, **connection_params)
    
    try:
        with connector:
            df = connector.execute_query(query)
            return df
    except Exception as e:
        logger.error(f"从数据库加载数据失败: {e}")
        raise
