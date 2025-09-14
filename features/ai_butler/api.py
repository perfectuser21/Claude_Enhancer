#!/usr/bin/env python3
"""
AI管家API接口
提供Web API和聊天接口
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn

from .butler import AIButler

logger = logging.getLogger("AI_Butler_API")

# 请求模型
class TaskRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str

class AIButlerAPI:
    """AI管家API类"""

    def __init__(self):
        """初始化API"""
        self.app = FastAPI(title="AI Butler API", description="VibePilot AI管家API")
        self.butler = AIButler()
        self.setup_middleware()
        self.setup_routes()

    def setup_middleware(self):
        """设置中间件"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        """设置路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """返回AI管家Web界面"""
            return HTMLResponse(content=self._get_web_interface(), media_type="text/html")

        @self.app.post("/chat")
        async def chat(request: ChatRequest):
            """聊天接口"""
            try:
                message = request.message.strip()
                if not message:
                    raise HTTPException(status_code=400, detail="消息不能为空")

                # 分析消息类型
                analysis = self.butler.analyze_user_message(message)

                if analysis["should_execute_claude"]:
                    # 执行Claude任务
                    logger.info(f"执行Claude任务: {message}")
                    result = await self.butler.execute_claude_task(message)

                    if result["success"]:
                        response = f"""✅ **任务执行成功**

📋 **任务**: {message}
⏱️ **执行时间**: {result['execution_time']:.1f}秒

📊 **Claude Code输出**:
```
{result['output']}
```"""

                        if result.get('stderr'):
                            response += f"\n\n⚠️ **注意信息**:\n```\n{result['stderr']}\n```"

                        return {
                            "success": True,
                            "response": response,
                            "status": f"✅ 任务完成 ({result['execution_time']:.1f}秒)",
                            "execution_details": result
                        }
                    else:
                        error_response = f"""❌ **任务执行失败**

📋 **任务**: {message}
🔸 **错误**: {result['error']}
⏱️ **执行时间**: {result.get('execution_time', 0):.1f}秒"""

                        if result.get('output'):
                            error_response += f"\n\n📝 **部分输出**:\n```\n{result['output']}\n```"

                        if result.get('stderr'):
                            error_response += f"\n\n🔍 **错误详情**:\n```\n{result['stderr']}\n```"

                        return {
                            "success": False,
                            "response": error_response,
                            "status": "❌ 任务失败",
                            "error": result['error']
                        }
                else:
                    # 普通聊天
                    response = self.butler.generate_chat_response(message)
                    return {
                        "success": True,
                        "response": response,
                        "status": "💬 对话中...",
                        "type": "chat"
                    }

            except Exception as e:
                logger.error(f"聊天处理失败: {e}")
                return {
                    "success": False,
                    "response": f"❌ 处理消息时出错: {str(e)}",
                    "status": "❌ 系统错误",
                    "error": str(e)
                }

        @self.app.get("/status")
        async def get_status():
            """获取管家状态"""
            return self.butler.get_session_stats()

        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    def _get_web_interface(self):
        """获取Web界面HTML"""
        html = '''
<!DOCTYPE html>
<html>
<head>
    <title>🤖 VibePilot AI Butler</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
        }
        .chat-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            height: 500px;
            display: flex;
            flex-direction: column;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            padding: 15px;
        }
        .message {
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 10px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user-message {
            background: linear-gradient(45deg, #667eea, #764ba2);
            margin-left: auto;
            text-align: right;
        }
        .butler-message {
            background: rgba(255, 255, 255, 0.2);
            margin-right: auto;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        input {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 16px;
        }
        input::placeholder { color: rgba(255, 255, 255, 0.7); }
        button {
            padding: 15px 25px;
            border: none;
            border-radius: 25px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { transform: translateY(-2px); }
        .status {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        .loading {
            background: rgba(255, 193, 7, 0.3);
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 VibePilot AI Butler</h1>
        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="butler-message message">
                    👋 你好！我是VibePilot的AI管家。我可以自动调用Claude Code来帮你处理各种编程任务，无需手动确认权限。
                    <br><br>
                    直接告诉我你需要做什么就行！
                </div>
            </div>
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="告诉我你需要做什么..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">发送</button>
            </div>
        </div>
        <div class="status" id="status">
            🟢 AI管家就绪，等待指令...
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            input.value = '';

            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = '🤖 管家正在处理...';
            document.getElementById('messages').appendChild(loadingDiv);

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });

                const data = await response.json();
                loadingDiv.remove();

                if (data.success) {
                    addMessage(data.response, 'butler');
                    updateStatus(data.status || '✅ 任务完成');
                } else {
                    addMessage('❌ 处理失败: ' + data.error, 'butler');
                    updateStatus('❌ 处理失败');
                }
            } catch (error) {
                loadingDiv.remove();
                addMessage('❌ 连接错误: ' + error.message, 'butler');
                updateStatus('❌ 连接错误');
            }
        }

        function addMessage(text, type) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.innerHTML = text.replace(/\\n/g, '<br>');
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function updateStatus(status) {
            document.getElementById('status').textContent = status;
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
    </script>
</body>
</html>
        '''

        return html

    def run(self, host="0.0.0.0", port=8001):
        """启动API服务器"""
        logger.info(f"🤖 启动AI Butler API服务器...")
        logger.info(f"🌐 Web界面: http://localhost:{port}")

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )