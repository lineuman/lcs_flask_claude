import re
import urllib.parse
import json

def convert_curl_to_python(curl_command):
    """
    将 curl 命令转换为 Python requests 代码
    """
    # 移除开头的 'curl' 和空白字符
    curl_command = curl_command.strip()
    if not curl_command.startswith('curl'):
        raise ValueError("不是有效的 curl 命令")
    
    # 初始化解析结果
    parsed = {
        'url': '',
        'method': 'GET',
        'headers': {},
        'data': None,
        'params': {},
        'auth': None,
        'verify_ssl': True
    }
    
    # 提取 URL
    url_match = re.search(r'curl\s+["\']?([^"\'\s]+)', curl_command)
    if not url_match:
        raise ValueError("无法解析 URL")
    parsed['url'] = url_match.group(1)
    
    # 解析各种选项
    options = re.findall(r'(-[A-Za-z]|--[a-zA-Z-]+)\s+([^\s-]+|"[^"]*"|\'[^\']*\')', curl_command)
    
    for option, value in options:
        value = value.strip('"\'')
        
        if option in ['-X', '--request']:
            parsed['method'] = value.upper()
        elif option in ['-H', '--header']:
            if ':' in value:
                key, val = value.split(':', 1)
                parsed['headers'][key.strip()] = val.strip()
        elif option in ['-d', '--data', '--data-raw']:
            parsed['data'] = value
            parsed['method'] = 'POST'  # 如果有数据，默认为 POST
        elif option in ['-u', '--user']:
            parsed['auth'] = value
        elif option in ['-k', '--insecure']:
            parsed['verify_ssl'] = False
        elif option in ['-G', '--get']:
            parsed['method'] = 'GET'
    
    # 生成 Python 代码
    lines = [
        "import requests",
        "",
        f"url = '{parsed['url']}'"
    ]
    
    # 处理查询参数
    if '?' in parsed['url']:
        base_url, query_string = parsed['url'].split('?', 1)
        lines[2] = f"url = '{base_url}'"
        params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, val = param.split('=', 1)
                params[key] = urllib.parse.unquote(val)
        if params:
            lines.append(f"params = {params}")
    
    # 处理请求头
    if parsed['headers']:
        lines.append(f"headers = {parsed['headers']}")
    
    # 处理数据
    if parsed['data']:
        try:
            # 尝试解析 JSON
            data_dict = json.loads(parsed['data'])
            lines.append(f"data = {data_dict}")
        except:
            # 如果不是 JSON，作为字符串处理
            lines.append(f"data = '{parsed['data']}'")
    
    # 处理认证
    if parsed['auth']:
        if ':' in parsed['auth']:
            username, password = parsed['auth'].split(':', 1)
            lines.append(f"auth = ('{username}', '{password}')")
    
    # 处理 SSL 验证
    if not parsed['verify_ssl']:
        lines.append("verify = False")
    
    lines.append("")
    
    # 生成请求调用
    request_line = f"response = requests.{parsed['method'].lower()}("
    request_args = []
    
    request_args.append("url")
    if 'params' in locals():
        request_args.append("params=params")
    if 'headers' in locals():
        request_args.append("headers=headers")
    if 'data' in locals():
        request_args.append("data=data")
    if 'auth' in locals():
        request_args.append("auth=auth")
    if not parsed['verify_ssl']:
        request_args.append("verify=verify")
    
    request_line += ", ".join(request_args) + ")"
    lines.append(request_line)
    
    lines.append("")
    lines.append("print(f'Status Code: {response.status_code}')")
    lines.append("print(f'Response: {response.text}')")
    
    return "\n".join(lines)