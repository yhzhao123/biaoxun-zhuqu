/**
 * 测试登录并获取Token
 * 在浏览器控制台中运行此脚本
 */

// 测试登录API
async function testLogin() {
  const API_URL = 'http://localhost:8000/api/v1';

  // 创建测试用户（如果还没有）
  // 先尝试登录
  const loginData = {
    username: 'testuser',
    password: 'testpass123'
  };

  try {
    console.log('正在登录...', loginData);

    const response = await fetch(`${API_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(loginData)
    });

    if (response.ok) {
      const data = await response.json();
      console.log('登录成功!');
      console.log('Token:', data.token);

      // 保存token到localStorage
      localStorage.setItem('token', data.token);
      console.log('Token已保存到localStorage');

      // 测试LLM API
      console.log('正在测试LLM API...');
      const llmResponse = await fetch(`${API_URL}/llm/configs/`, {
        headers: {
          'Authorization': `Token ${data.token}`
        }
      });

      if (llmResponse.ok) {
        const llmData = await llmResponse.json();
        console.log('LLM API测试成功!');
        console.log('Configs:', llmData);
      } else {
        console.error('LLM API测试失败:', llmResponse.status, llmResponse.statusText);
      }

      return data.token;
    } else {
      const error = await response.json();
      console.error('登录失败:', error);

      // 如果登录失败，提示需要在后端创建用户
      console.log('');
      console.log('=================================');
      console.log('需要在后端创建测试用户');
      console.log('运行命令: python manage.py shell < scripts/create_test_user.py');
      console.log('=================================');

      return null;
    }
  } catch (error) {
    console.error('请求错误:', error);
    return null;
  }
}

// 检查当前token状态
function checkTokenStatus() {
  const token = localStorage.getItem('token');
  if (token) {
    console.log('当前Token:', token);
    console.log('Token已存储在localStorage中');
  } else {
    console.log('未找到Token，请先运行 testLogin()');
  }
  return token;
}

// 清除token
function clearToken() {
  localStorage.removeItem('token');
  console.log('Token已清除');
}

// 导出函数供控制台使用
window.testLogin = testLogin;
window.checkTokenStatus = checkTokenStatus;
window.clearToken = clearToken;

console.log('=== 登录测试脚本已加载 ===');
console.log('可用函数:');
console.log('- testLogin(): 测试登录并获取token');
console.log('- checkTokenStatus(): 检查当前token状态');
console.log('- clearToken(): 清除token');
console.log('');
console.log('使用方法:');
console.log('1. 在浏览器控制台运行: testLogin()');
console.log('2. 或者在需要token的页面直接运行:');
console.log('   localStorage.setItem("token", "你的token值");');
