"""
自动化冒烟测试脚本
使用 selenium 自动遍历所有菜单和功能，检查是否有JavaScript错误
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
from datetime import datetime

class AutoTester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.errors = []
        self.screenshots = []
        
        # 配置Chrome选项
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 无头模式，不需要显示窗口
        chrome_options.add_argument('--start-maximized')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def take_screenshot(self, name):
        """截图保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'output/screenshots/{name}_{timestamp}.png'
        self.driver.save_screenshot(filename)
        self.screenshots.append(filename)
        print(f'📸 截图已保存: {filename}')
        return filename
    
    def log_error(self, message):
        """记录错误"""
        self.errors.append({
            'time': datetime.now().isoformat(),
            'message': message,
            'url': self.driver.current_url
        })
        print(f'❌ 错误: {message}')
    
    def click_element(self, selector, description):
        """点击元素并捕获错误"""
        try:
            print(f'🖱️  点击: {description} ({selector})')
            element = self.wait.until(EC.element_to_be_clickable(selector))
            element.click()
            time.sleep(1)  # 等待页面加载
            
            # 检查是否有错误弹窗（红色消息栏）
            try:
                error_toast = self.driver.find_element(By.CSS_SELECTOR, '.toast.error')
                if error_toast.is_displayed():
                    error_text = error_toast.text
                    self.log_error(f"页面弹出错误: {error_text}")
                    self.take_screenshot(f'error_{description}')
            except NoSuchElementException:
                pass
                
            return True
        except Exception as e:
            self.log_error(f"点击 {description} 失败: {str(e)}")
            self.take_screenshot(f'error_{description}')
            return False
    
    def test_navigation(self):
        """测试所有导航菜单"""
        print("\n🚀 开始测试导航菜单...")
        
        menus = [
            (By.LINK_TEXT, '质量大盘', '质量大盘'),
            (By.LINK_TEXT, '资产管理', '资产管理'),
            (By.LINK_TEXT, '规则配置', '规则配置'),
            (By.LINK_TEXT, '规则管理', '规则管理'),
            (By.LINK_TEXT, '运行管理', '运行管理'),
            (By.LINK_TEXT, '问题管理', '问题管理'),
        ]
        
        for selector_type, selector_text, description in menus:
            self.click_element((selector_type, selector_text), description)
    
    def test_asset_management(self):
        """测试资产管理页面功能"""
        print("\n📦 测试资产管理...")
        self.click_element((By.LINK_TEXT, '资产管理'), '资产管理菜单')
        
        # 测试搜索
        try:
            search_input = self.driver.find_element(By.ID, 'search-input')
            search_input.send_keys('test')
            print('✓ 搜索框输入正常')
            time.sleep(1)
        except Exception as e:
            self.log_error(f"搜索框测试失败: {str(e)}")
        
        # 测试新建资产按钮
        self.click_element((By.XPATH, "//button[contains(text(), '新建资产')]"), '新建资产按钮')
        # 关闭模态框
        try:
            close_btn = self.driver.find_element(By.CLASS_NAME, 'close')
            close_btn.click()
            time.sleep(0.5)
        except:
            pass
    
    def test_rule_management(self):
        """测试规则管理页面功能"""
        print("\n📏 测试规则管理...")
        self.click_element((By.LINK_TEXT, '规则管理'), '规则管理菜单')
        time.sleep(1)
    
    def test_execution_management(self):
        """测试运行管理页面"""
        print("\n⚡ 测试运行管理...")
        self.click_element((By.LINK_TEXT, '运行管理'), '运行管理菜单')
        time.sleep(1)
    
    def run_all_tests(self):
        """运行所有测试"""
        try:
            print(f'🌐 访问: {self.base_url}')
            self.driver.get(self.base_url)
            time.sleep(2)
            
            self.take_screenshot('homepage')
            
            # 依次测试
            self.test_navigation()
            self.test_asset_management()
            self.test_rule_management()
            self.test_execution_management()
            
            print("\n✅ 所有测试完成!")
            print(f"📊 总计错误: {len(self.errors)}")
            print(f"📸 截图数量: {len(self.screenshots)}")
            
            if self.errors:
                print("\n❌ 错误列表:")
                for i, err in enumerate(self.errors, 1):
                    print(f"  {i}. [{err['time']}] {err['message']} at {err['url']}")
            
            # 保存报告
            with open('output/test_report.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'errors': self.errors,
                    'screenshots': self.screenshots,
                    'total_errors': len(self.errors),
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            print("\n📝 报告已保存到: output/test_report.json")
            
        except Exception as e:
            self.log_error(f"测试运行异常: {str(e)}")
            self.take_screenshot('fatal_error')
        finally:
            self.driver.quit()

if __name__ == '__main__':
    import sys
    import os
    
    # 创建截图目录
    os.makedirs('output/screenshots', exist_ok=True)
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5000'
    tester = AutoTester(base_url)
    tester.run_all_tests()
