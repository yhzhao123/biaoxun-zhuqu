#!/usr/bin/env python
"""
LLM连接诊断脚本
检查各种LLM提供商的连接状态
"""

import os
import sys
import requests
from typing import Dict, Tuple

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_ollama(base_url: str = "http://localhost:11434") -> Tuple[bool, str, list]:
    """检查Ollama连接状态"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            return True, f"连接成功，可用模型: {model_names}", model_names
        else:
            return False, f"HTTP状态码: {response.status_code}", []
    except requests.exceptions.ConnectionError:
        return False, "无法连接 - 请确认Ollama服务是否运行 (运行 'ollama serve')", []
    except requests.exceptions.Timeout:
        return False, "连接超时", []
    except Exception as e:
        return False, f"错误: {str(e)}", []


def check_openai(api_key: str = None) -> Tuple[bool, str]:
    """检查OpenAI连接状态"""
    if not api_key:
        api_key = os.environ.get('OPENAI_API_KEY')

    if not api_key:
        return False, "未配置API密钥 (设置环境变量 OPENAI_API_KEY)"

    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        if response.status_code == 200:
            return True, "连接成功"
        elif response.status_code == 401:
            return False, "API密钥无效"
        else:
            return False, f"HTTP状态码: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "无法连接到OpenAI服务器"
    except Exception as e:
        return False, f"错误: {str(e)}"


def check_claude(api_key: str = None) -> Tuple[bool, str]:
    """检查Claude连接状态"""
    if not api_key:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        return False, "未配置API密钥 (设置环境变量 ANTHROPIC_API_KEY)"

    try:
        response = requests.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            timeout=10
        )
        if response.status_code == 200:
            return True, "连接成功"
        elif response.status_code == 401:
            return False, "API密钥无效"
        else:
            return False, f"HTTP状态码: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "无法连接到Anthropic服务器"
    except Exception as e:
        return False, f"错误: {str(e)}"


def test_llm_chat(provider: str, base_url: str = None, api_key: str = None, model: str = None) -> Tuple[bool, str]:
    """测试LLM聊天功能"""
    test_message = "回复'OK'两个字符"

    try:
        if provider == 'ollama':
            url = f"{base_url or 'http://localhost:11434'}/api/chat"
            data = {
                "model": model or "qwen2.5:7b",
                "messages": [{"role": "user", "content": test_message}],
                "stream": False
            }
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result.get('message', {}).get('content', '')
            return True, f"响应: {content[:50]}..."

        elif provider == 'openai':
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model or "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": test_message}],
                "max_tokens": 50
            }
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            return True, f"响应: {content[:50]}..."

        elif provider == 'claude':
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            data = {
                "model": model or "claude-3-haiku-20240307",
                "max_tokens": 50,
                "messages": [{"role": "user", "content": test_message}]
            }
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result['content'][0]['text']
            return True, f"响应: {content[:50]}..."

        else:
            return False, f"未知提供商: {provider}"

    except requests.exceptions.ConnectionError:
        return False, "连接失败"
    except requests.exceptions.Timeout:
        return False, "请求超时"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP错误: {e.response.status_code} - {e.response.text[:100]}"
    except Exception as e:
        return False, f"错误: {str(e)}"


def main():
    # 设置输出编码
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 60)
    print("LLM 连接诊断报告")
    print("=" * 60)

    # 检查Ollama
    print("\n[1] Ollama (本地模型)")
    print("-" * 40)
    ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    success, message, models = check_ollama(ollama_url)
    status = "[OK]" if success else "[FAIL]"
    print(f"状态: {status} {message}")

    if success and models:
        print("\n可用模型:")
        for m in models:
            print(f"  - {m}")

        # 测试聊天
        print("\n测试聊天功能...")
        model = next((m for m in models if 'qwen' in m or 'llama' in m), models[0])
        chat_success, chat_msg = test_llm_chat('ollama', ollama_url, None, model)
        chat_status = "[OK]" if chat_success else "[FAIL]"
        print(f"聊天测试: {chat_status} {chat_msg}")

    # 检查OpenAI
    print("\n[2] OpenAI")
    print("-" * 40)
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        print(f"API密钥: 已配置 ({openai_key[:8]}...)")
    success, message = check_openai()
    status = "[OK]" if success else "[FAIL]"
    print(f"状态: {status} {message}")

    if success:
        print("\n测试聊天功能...")
        chat_success, chat_msg = test_llm_chat('openai', None, openai_key)
        chat_status = "[OK]" if chat_success else "[FAIL]"
        print(f"聊天测试: {chat_status} {chat_msg}")

    # 检查Claude
    print("\n[3] Claude (Anthropic)")
    print("-" * 40)
    claude_key = os.environ.get('ANTHROPIC_API_KEY')
    if claude_key:
        print(f"API密钥: 已配置 ({claude_key[:8]}...)")
    success, message = check_claude()
    status = "[OK]" if success else "[FAIL]"
    print(f"状态: {status} {message}")

    if success:
        print("\n测试聊天功能...")
        chat_success, chat_msg = test_llm_chat('claude', None, claude_key)
        chat_status = "[OK]" if chat_success else "[FAIL]"
        print(f"聊天测试: {chat_status} {chat_msg}")

    # 总结
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

    # 建议
    print("\n建议:")
    if not check_ollama(ollama_url)[0]:
        print("  1. 启动Ollama: 运行 'ollama serve'")
        print("  2. 或配置OpenAI/Claude API密钥作为替代方案")

    if not os.environ.get('OPENAI_API_KEY') and not os.environ.get('ANTHROPIC_API_KEY'):
        print("  3. 设置环境变量:")
        print("     - OPENAI_API_KEY=your-key")
        print("     - ANTHROPIC_API_KEY=your-key")


if __name__ == '__main__':
    main()