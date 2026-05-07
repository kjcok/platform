"""
自动化冒烟测试脚本 (Playwright 版本)
使用 Playwright 自动遍历所有菜单和功能，检查是否有JavaScript错误
Playwright 比 Selenium 更现代化，更稳定
"""

from playwright.sync_api import sync_playwright, Expect
from datetime import datetime
import json
import os

class AutoTester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.errors = []
        self.screenshots = []
    
    def take_screenshot(self, page, name):
        """截图保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'output/screenshots/{name}_{timestamp}.png'
        page.screenshot(path=filename, full_page=True)
        self.screenshots.append(filename)
        print(f'📸 截图已保存: {filename}')
        return filename
    
    def log_error(self, message, url):
        """记录错误"""
        self.errors.append({
            'time': datetime.now().isoformat(),
            'message': message,
            'url': url
        })
        print(f'❌ 错误: {message}')
    
    def check_for_error_toast(self, page):
        """检查是否有错误弹窗（红色消息栏）"""
        try:
            error_toast = page.locator('.toast.error')
            if error_toast.is_visible():
                error_text = error_toast.inner_text()
                self.log_error(f"页面弹出错误: {error_text}", page.url)
                self.take_screenshot(page, f'error_toast')
                return True
            return False
        except Exception:
            return False
    
    def click_element(self, page, selector, description):
        """点击元素并捕获错误"""
        try:
            print(f'🖱️  点击: {description} ({selector})')
            page.locator(selector).click(timeout=5000)
            page.wait_for_load_state('networkidle', timeout=5000)
            page.wait_for_timeout(1000)
            
            self.check_for_error_toast(page)
            return True
        except Exception as e:
            self.log_error(f"点击 {description} 失败: {str(e)}", page.url)
            self.take_screenshot(page, f'error_{description.replace(" ", "_")}')
            return False
    
    def test_navigation(self, page):
        """测试所有导航菜单"""
        print("\n🚀 开始测试导航菜单...")
        
        menus = [
            ('nav a:text("质量大盘")', '质量大盘'),
            ('nav a:text("资产管理")', '资产管理'),
            ('nav a:text("规则配置")', '规则配置'),
            ('nav a:text("规则管理")', '规则管理'),
            ('nav a:text("运行管理")', '运行管理'),
            ('nav a:text("问题管理")', '问题管理'),
            ('nav a:text("校验历史")', '校验历史'),
        ]
        
        for selector, description in menus:
            self.click_element(page, selector, description)
    
    def test_asset_management(self, page):
        """测试资产管理页面功能"""
        print("\n📦 测试资产管理...")
        
        # 已经在资产管理页面
        try:
            # 测试搜索
            search_input = page.locator('#search-input')
            if search_input.is_visible():
                search_input.fill('test')
                page.wait_for_timeout(500)
                print('✓ 搜索框输入正常')
        except Exception as e:
            self.log_error(f"搜索框测试失败: {str(e)}", page.url)
        
        # 测试新建资产按钮
        self.click_element(page, 'button:has-text("+ 新建资产")', '新建资产按钮')
        
        # 关闭模态框
        try:
            close_btn = page.locator('.close')
            if close_btn.is_visible():
                close_btn.click()
                page.wait_for_timeout(500)
        except:
            pass
    
    def test_rule_management(self, page):
        """测试规则管理页面功能"""
        print("\n📏 测试规则管理...")
        page.wait_for_timeout(1000)
        
        # 检查表格是否加载
        try:
            tbody = page.locator('#rules-table-body')
            if tbody.is_visible():
                print('✓ 规则列表加载正常')
        except Exception as e:
            self.log_error(f"规则列表加载失败: {str(e)}", page.url)
    
    def test_execution_management(self, page):
        """测试运行管理页面"""
        print("\n⚡ 测试运行管理...")
        page.wait_for_timeout(1000)
        
        # 检查页面元素
        try:
            batch_btn = page.locator('button:has-text("批量运行选中资产")')
            if batch_btn.is_visible():
                print('✓ 运行管理页面加载正常')
        except Exception as e:
            self.log_error(f"运行管理页面加载失败: {str(e)}", page.url)
    
    def test_rule_config_v2(self, page):
        """测试规则配置 v2 页面"""
        print("\n🎨 测试规则配置页面（二级菜单）...")
        
        # 已经在规则配置页面
        page.wait_for_timeout(1000)
        
        # 测试展开分类
        categories = [
            'column_values',
            'column_aggregates', 
            'table',
            'column_pairs',
            'multicolumn',
            'datetime',
            'json'
        ]
        
        for category_id in categories:
            try:
                selector = f'#{category_id}'
                category = page.locator(selector)
                if category.is_visible():
                    category.click()
                    page.wait_for_timeout(300)
                    print(f'✓ 展开分类 {category_id}')
                    self.check_for_error_toast(page)
            except Exception as e:
                self.log_error(f"展开分类 {category_id} 失败: {str(e)}", page.url)
    
    def run_all_tests(self):
        """运行所有测试"""
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            # 监听控制台错误
            page.on('console', lambda msg: 
                self.log_error(f"Console {msg.type}: {msg.text}", page.url) 
                if msg.type == 'error' else None
            )
            
            try:
                print(f'🌐 访问: {self.base_url}')
                page.goto(self.base_url, wait_until='networkidle')
                page.wait_for_timeout(2000)
                
                self.take_screenshot(page, 'homepage')
                
                # 依次测试
                self.test_navigation(page)
                
                page.goto(f"{self.base_url}/assets", wait_until='networkidle')
                page.wait_for_timeout(1000)
                self.test_asset_management(page)
                
                page.goto(f"{self.base_url}/rule-management", wait_until='networkidle')
                page.wait_for_timeout(1000)
                self.test_rule_management(page)
                
                page.goto(f"{self.base_url}/rule-config", wait_until='networkidle')
                page.wait_for_timeout(1000)
                self.test_rule_config_v2(page)
                
                page.goto(f"{self.base_url}/execution-management", wait_until='networkidle')
                page.wait_for_timeout(1000)
                self.test_execution_management(page)
                
                print("\n✅ 所有测试完成!")
                print(f"📊 总计错误: {len(self.errors)}")
                print(f"📸 截图数量: {len(self.screenshots)}")
                
                if self.errors:
                    print("\n❌ 错误列表:")
                    for i, err in enumerate(self.errors, 1):
                        print(f"  {i}. [{err['time']}] {err['message']} at {err['url']}")
                
                # 保存报告
                with open('output/test_report_playwright.json', 'w', encoding='utf-8') as f:
                    json.dump({
                        'errors': self.errors,
                        'screenshots': self.screenshots,
                        'total_errors': len(self.errors),
                        'timestamp': datetime.now().isoformat()
                    }, f, ensure_ascii=False, indent=2)
                
                print("\n📝 报告已保存到: output/test_report_playwright.json")
                
            except Exception as e:
                self.log_error(f"测试运行异常: {str(e)}", page.url)
                self.take_screenshot(page, 'fatal_error')
            finally:
                context.close()
                browser.close()

if __name__ == '__main__':
    import sys
    
    # 创建截图目录
    os.makedirs('output/screenshots', exist_ok=True)
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5000'
    tester = AutoTester(base_url)
    tester.run_all_tests()
