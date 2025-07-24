import requests
import random
import time
from tqdm import tqdm

# ============== 配置区域 ==============
TOTAL_REQUESTS = 100      # 总请求次数
TARGET_URL = "http://example.com"  # 测试目标地址
REQUEST_INTERVAL = 0.1    # 请求间隔（秒）
MIN_PASSWORD_LENGTH = 8   # 最小密码长度
MAX_PASSWORD_LENGTH = 16  # 最大密码长度
# ====================================

# 法律声明（使用前请阅读）
LEGAL_NOTICE = """
※ 注意事项 ※
1. 仅限本地测试使用
2. 请勿对非自有网站发起请求
3. 高频请求可能导致IP被封禁
4. 禁止用于非法用途
"""
print(LEGAL_NOTICE)

def generate_fake_account():
    """生成有趣的测试账户"""
    adjectives = ['Happy', 'Silly', 'Crazy', 'Magic']
    nouns = ['Panda', 'Unicorn', 'Wizard', 'Dragon']
    domains = ['test', 'demo', 'play', 'fake']
    
    username = f"{random.choice(adjectives)}_{random.choice(nouns)}_{random.randint(100,999)}"
    password = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*", 
                    k=random.randint(MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH)))
    return username, password

def send_playful_request(url):
    """发送带有随机参数的测试请求"""
    try:
        # 生成随机参数
        params = {
            'user': generate_fake_account()[0],
            'pass': generate_fake_account()[1],
            'test_id': random.randint(1000,9999),
            'source': random.choice(['mobile', 'desktop', 'tablet'])
        }
        
        # 添加随机请求头
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (PlayStation; like Nintendo)',
                'ToiletBrowser/1.0 (Running on SmartToiletOS)',
                'MagicWand/2.1 (Wizarding Web Client)'
            ]),
            'X-Test-Mode': 'playful'
        }
        
        response = requests.get(
            url=url,
            params=params,
            headers=headers,
            timeout=3
        )
        
        return {
            'status': response.status_code,
            'size': len(response.content),
            'time': response.elapsed.total_seconds()
        }
        
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    results = []
    
    # 创建进度条
    with tqdm(total=TOTAL_REQUESTS, desc="测试进度") as pbar:
        for _ in range(TOTAL_REQUESTS):
            # 发送请求并记录结果
            result = send_playful_request(TARGET_URL)
            results.append(result)
            
            # 更新进度条描述
            if 'error' in result:
                pbar.set_postfix_str(f"最新错误：{result['error'][:20]}")
            else:
                pbar.set_postfix_str(f"状态码：{result['status']} 响应时间：{result['time']:.2f}s")
            
            pbar.update(1)
            time.sleep(REQUEST_INTERVAL)
    
    # 生成统计报告
    success = sum(1 for r in results if 'status' in r and r['status'] == 200)
    avg_time = sum(r.get('time',0) for r in results) / len(results)
    
    print("\n=== 测试报告 ===")
    print(f"成功请求：{success}/{TOTAL_REQUESTS} ({success/TOTAL_REQUESTS:.1%})")
    print(f"平均响应时间：{avg_time:.2f}秒")
    print(f"最大响应大小：{max(r.get('size',0) for r in results)} bytes")
    print("趣味请求示例：")
    print(f"用户名：{generate_fake_account()[0]}")
    print(f"密码：{generate_fake_account()[1]}")
