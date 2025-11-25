#!/usr/bin/env python3
"""
检查是否有多个应用进程在运行，可能导致重复推送
"""
import subprocess
import sys
import os

def check_running_processes():
    """检查是否有多个应用进程在运行"""
    if sys.platform == "win32":
        # Windows
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            lines = result.stdout.strip().split('\n')
            python_processes = [line for line in lines if 'python.exe' in line.lower()]
            print(f"发现 {len(python_processes)} 个 Python 进程:")
            for i, proc in enumerate(python_processes, 1):
                print(f"  {i}. {proc}")
            
            # 检查是否有 uvicorn 进程
            result2 = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe", "/V"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            uvicorn_count = result2.stdout.lower().count('uvicorn')
            if uvicorn_count > 0:
                print(f"\n⚠️  警告：发现 {uvicorn_count} 个可能包含 uvicorn 的进程")
                print("   这可能导致多个调度器实例同时运行！")
                return True
        except Exception as e:
            print(f"检查进程时出错: {e}")
    else:
        # Linux/Mac
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            uvicorn_lines = [line for line in result.stdout.split('\n') if 'uvicorn' in line.lower() and 'app.main:app' in line]
            if len(uvicorn_lines) > 1:
                print(f"⚠️  警告：发现 {len(uvicorn_lines)} 个 uvicorn 进程:")
                for i, line in enumerate(uvicorn_lines, 1):
                    print(f"  {i}. {line}")
                return True
            elif len(uvicorn_lines) == 1:
                print(f"✓ 只发现 1 个 uvicorn 进程（正常）")
                return False
            else:
                print("未发现运行中的 uvicorn 进程")
                return False
        except Exception as e:
            print(f"检查进程时出错: {e}")
    
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("检查重复进程")
    print("=" * 60)
    has_duplicate = check_running_processes()
    print("\n" + "=" * 60)
    if has_duplicate:
        print("建议：")
        print("1. 停止所有运行中的应用实例")
        print("2. 只启动一个应用实例")
        print("3. 检查是否有 systemd、supervisor 等服务管理工具启动了多个实例")
    else:
        print("未发现重复进程，问题可能在其他地方")
    print("=" * 60)



