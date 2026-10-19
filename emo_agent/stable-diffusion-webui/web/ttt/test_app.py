from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'status': 'ok', 'message': '测试成功'})

@app.route('/health')
def health():
    return 'Healthy'

if __name__ == '__main__':
    print('=' * 50)
    print(' 启动测试服务器...')
    print(' 访问: http://localhost:5000')
    print('=' * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
