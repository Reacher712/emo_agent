# kling_backend.py - 简化CORS版本
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import time
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 方式1：使用 flask-cors 的最简配置（推荐）
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 方式2：或者使用全局配置
# CORS(app, supports_credentials=True)

# ========== 删除所有其他的CORS配置 ==========
# 不要使用 @app.after_request
# 不要在路由中手动添加CORS头
# 不要单独处理OPTIONS请求（除非有特殊需求）

ACCESS_KEY = os.getenv('KLING_ACCESS_KEY', 'AnGkPmy3YGpJntm8EC3AEHnfQfpfkRhK')
SECRET_KEY = os.getenv('KLING_SECRET_KEY', 'DyJB8FkF9tJmRTCaH3MKkCFedYhfkmHp')

def generate_kling_token():
    """生成可灵API的JWT Token"""
    try:
        payload = {
            "iss": ACCESS_KEY,
            "nbf": int(time.time()),
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "aud": "kling-api"
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    except Exception as e:
        print(f"Token生成失败: {e}")
        return None

@app.route('/')
def index():
    return jsonify({
        'service': 'Kling AI Video Generator',
        'status': 'running'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['image']
        file_bytes = file.read()
        base64_data = base64.b64encode(file_bytes).decode('utf-8')
        
        return jsonify({
            'success': True,
            'base64': base64_data,
            'filename': file.filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """生成视频"""
    try:
        # 获取数据
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        image_base64 = data.get('image', '')
        prompt = data.get('prompt', '').strip()
        mode = data.get('mode', 'std')
        duration = data.get('duration', '5')
        
        # 如果是文件上传
        if 'image' in request.files:
            file = request.files['image']
            file_bytes = file.read()
            image_base64 = base64.b64encode(file_bytes).decode('utf-8')
        
        if not image_base64:
            return jsonify({'success': False, 'error': '缺少图片数据'}), 400
        
        if not prompt:
            return jsonify({'success': False, 'error': '请输入视频描述'}), 400
        
        # 清理Base64前缀
        if image_base64.startswith('data:'):
            image_base64 = image_base64.split(',', 1)[1]
        
        # 生成Token
        token = generate_kling_token()
        if not token:
            return jsonify({'success': False, 'error': 'Token生成失败'}), 500
        
        # 调用可灵API
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        request_body = {
            'model_name': 'kling-v1',
            'image': image_base64,
            'prompt': prompt[:2000],
            'mode': mode,
            'duration': duration,
            'cfg_scale': 0.5
        }
        
        response = requests.post(
            'https://api-beijing.klingai.com/v1/videos/image2video',
            headers=headers,
            json=request_body,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('data', {}).get('task_id')
            
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': '视频生成任务已提交'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'API调用失败: {response.status_code}',
                'response': response.text[:500]
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    try:
        token = generate_kling_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'https://api-beijing.klingai.com/v1/videos/image2video/{task_id}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'查询失败: {response.text}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 启动可灵AI后端服务...")
    print("📡 访问: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)