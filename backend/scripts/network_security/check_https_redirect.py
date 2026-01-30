#!/usr/bin/env python3
"""
检测用例：web服务支持https请求，且输入http请求能重定向到https

检测逻辑：
1. 检测目标是否支持 HTTPS 访问
2. 检测 HTTP 请求是否会重定向到 HTTPS

返回码：
- 0: 通过（支持 HTTPS 且 HTTP 会重定向到 HTTPS）
- 1: 失败（不支持 HTTPS 或 HTTP 不会重定向）
- 2: 错误（无法连接或其他异常）
"""

import sys
import urllib.request
import urllib.error
import ssl
import socket

# 超时设置（秒）
TIMEOUT = 10


def check_https_support(ip: str) -> tuple[bool, str]:
    """
    检测目标是否支持 HTTPS 访问
    
    Returns:
        (is_supported, message)
    """
    url = f"https://{ip}/"
    
    # 创建不验证证书的 SSL 上下文（因为可能是自签名证书）
    # 同时降低安全级别以兼容使用弱 DH 密钥的服务器
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
    
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'AutoSecDet/1.0')
        
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as response:
            return True, f"HTTPS 访问成功，状态码: {response.status}"
    except urllib.error.HTTPError as e:
        # HTTP 错误也说明 HTTPS 服务是可用的
        return True, f"HTTPS 服务可用，返回状态码: {e.code}"
    except urllib.error.URLError as e:
        if isinstance(e.reason, ssl.SSLError):
            return False, f"SSL 错误: {e.reason}"
        elif isinstance(e.reason, socket.timeout):
            return False, f"连接超时"
        else:
            return False, f"无法连接 HTTPS: {e.reason}"
    except socket.timeout:
        return False, "连接超时"
    except Exception as e:
        return False, f"HTTPS 检测异常: {str(e)}"


def check_http_redirect(ip: str) -> tuple[bool, str]:
    """
    检测 HTTP 请求是否重定向到 HTTPS
    
    Returns:
        (is_redirected, message)
    """
    url = f"http://{ip}/"
    
    try:
        # 创建不自动跟随重定向的 opener
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                # 不跟随重定向，返回 None
                return None
        
        opener = urllib.request.build_opener(NoRedirectHandler())
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', 'AutoSecDet/1.0')
        
        try:
            response = opener.open(req, timeout=TIMEOUT)
            # 如果没有重定向，返回失败
            return False, f"HTTP 请求返回 {response.status}，未重定向到 HTTPS"
        except urllib.error.HTTPError as e:
            # 检查是否是重定向响应
            if e.code in (301, 302, 303, 307, 308):
                location = e.headers.get('Location', '')
                if location.lower().startswith('https://'):
                    return True, f"HTTP 重定向到 HTTPS: {location} (状态码: {e.code})"
                else:
                    return False, f"HTTP 重定向但目标不是 HTTPS: {location}"
            else:
                return False, f"HTTP 请求返回错误 {e.code}，未重定向"
                
    except urllib.error.URLError as e:
        if isinstance(e.reason, socket.timeout):
            return False, "HTTP 连接超时"
        # 连接被拒绝可能意味着 HTTP 端口未开放（可能只开放 HTTPS）
        if "Connection refused" in str(e.reason):
            return False, "HTTP 端口 (80) 未开放，无法检测重定向"
        return False, f"HTTP 连接失败: {e.reason}"
    except socket.timeout:
        return False, "HTTP 连接超时"
    except Exception as e:
        return False, f"HTTP 检测异常: {str(e)}"


def main():
    if len(sys.argv) < 2:
        print("用法: python check_https_redirect.py <target_ip>")
        sys.exit(2)
    
    target_ip = sys.argv[1]
    print(f"目标 IP: {target_ip}")
    print("=" * 50)
    
    # 检测 1: HTTPS 支持
    print("\n[检测 1] 检测 HTTPS 支持...")
    https_ok, https_msg = check_https_support(target_ip)
    print(f"  结果: {'✓ 通过' if https_ok else '✗ 失败'}")
    print(f"  详情: {https_msg}")
    
    if not https_ok:
        print("\n" + "=" * 50)
        print("最终结果: ✗ 失败")
        print("原因: 目标不支持 HTTPS 访问")
        sys.exit(1)
    
    # 检测 2: HTTP 重定向
    print("\n[检测 2] 检测 HTTP 到 HTTPS 重定向...")
    redirect_ok, redirect_msg = check_http_redirect(target_ip)
    print(f"  结果: {'✓ 通过' if redirect_ok else '✗ 失败'}")
    print(f"  详情: {redirect_msg}")
    
    print("\n" + "=" * 50)
    
    if https_ok and redirect_ok:
        print("最终结果: ✓ 通过")
        print("说明: 目标支持 HTTPS，且 HTTP 请求会重定向到 HTTPS")
        sys.exit(0)
    else:
        print("最终结果: ✗ 失败")
        if not redirect_ok:
            print("原因: HTTP 请求未重定向到 HTTPS")
        sys.exit(1)


if __name__ == "__main__":
    main()
