#!/usr/bin/env python3
"""
简单的 CORS 代理服务器
用于解决可灵 API 的 CORS 问题
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json

class CORSProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """处理 GET 请求（用于轮询任务状态）"""
        if self.path.startswith('/proxy/kling'):
            # 处理两种情况：
            # 1. /proxy/kling/{task_id} - 查询任务状态
            # 2. /proxy/kling/ - 根路径（返回错误）
            
            if self.path == '/proxy/kling' or self.path == '/proxy/kling/':
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({'error': '缺少 task_id 参数'}).encode()
                self.wfile.write(error_response)
                return
            
            # 提取 task_id
            task_id = self.path.replace('/proxy/kling/', '').replace('/proxy/kling', '')
            if not task_id:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                return
            
            try:
                # 转发请求到可灵 API
                api_url = f'https://api-beijing.klingai.com/v1/videos/image2video/{task_id}'
                req = urllib.request.Request(
                    api_url,
                    headers={
                        'Authorization': self.headers.get('Authorization', '')
                    }
                )
                
                with urllib.request.urlopen(req) as response:
                    result = response.read()
                    
                    # 返回响应，添加 CORS 头
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(result)
            except Exception as e:
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({'error': str(e)}).encode()
                self.wfile.write(error_response)
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """处理 POST 请求（用于创建任务）"""
        if self.path.startswith('/proxy/kling'):
            # 代理可灵 API 请求
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                # 转发请求到可灵 API
                req = urllib.request.Request(
                    'https://api-beijing.klingai.com/v1/videos/image2video',
                    data=post_data,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': self.headers.get('Authorization', '')
                    }
                )
                
                with urllib.request.urlopen(req) as response:
                    result = response.read()
                    
                    # 返回响应，添加 CORS 头
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(result)
            except Exception as e:
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({'error': str(e)}).encode()
                self.wfile.write(error_response)
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass

if __name__ == '__main__':
    port = 8888
    server = HTTPServer(('localhost', port), CORSProxyHandler)
    print(f'🚀 CORS 代理服务器已启动')
    print(f'📡 监听地址: http://localhost:{port}')
    print(f'🔗 代理端点: http://localhost:{port}/proxy/kling')
    print(f'⚠️  按 Ctrl+C 停止服务器')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n👋 服务器已停止')
        server.shutdown()

