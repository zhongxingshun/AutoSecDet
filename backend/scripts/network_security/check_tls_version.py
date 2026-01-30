#!/usr/bin/env python3
"""
检测用例：web服务只支持TLS1.2+以上（包含）的协议，且不使用不安全的加密组件

检测逻辑：
1. 使用 nmap 的 ssl-enum-ciphers 脚本扫描目标支持的 SSL/TLS 协议
2. 检查是否存在不安全的协议（SSLv2, SSLv3, TLSv1.0, TLSv1.1）
3. 检查是否支持安全的协议（TLSv1.2, TLSv1.3）
4. 检查是否使用不安全的加密套件（3DES, RC4, DES, NULL, EXPORT 等）
5. 检查是否存在弱密钥交换（DH 1024 位以下）

返回码：
- 0: 通过（只支持 TLS 1.2+ 且无不安全加密组件）
- 1: 失败（支持不安全的协议或加密组件）
- 2: 错误（无法连接或其他异常）
"""

import sys
import subprocess
import re

# 超时设置（秒）
TIMEOUT = 60

# 不安全的协议列表
INSECURE_PROTOCOLS = ['SSLv2', 'SSLv3', 'TLSv1.0', 'TLSv1.1']

# 安全的协议列表
SECURE_PROTOCOLS = ['TLSv1.2', 'TLSv1.3']

# 不安全的加密套件关键字
INSECURE_CIPHERS = [
    '3DES', 'DES', 'RC4', 'RC2', 'NULL', 'EXPORT', 'anon', 'MD5'
]

# 常见 HTTPS 端口（用于快速扫描）
COMMON_HTTPS_PORTS = [443, 8443, 8081, 9443, 8080, 4443, 8444, 9000]

# 扫描端口列表（最常见的 SSL/HTTPS 端口，精简版以加快扫描）
SCAN_PORTS = "80,443,8080,8081,8443,9443"


def discover_ssl_ports(ip: str) -> tuple[bool, list, str]:
    """
    自动发现目标的所有 SSL/HTTPS 端口
    
    快速扫描常见端口，只检测端口是否开放（不做服务版本检测）
    
    Returns:
        (success, ports_list, message)
    """
    try:
        print(f"  正在快速扫描常见端口...")
        
        # 只做端口开放检测，不做服务版本检测（更快）
        cmd = [
            'nmap', '-sT', '-T5', '--open',  # -T5 最快速度
            '-p', SCAN_PORTS, ip
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        open_ports = []
        
        for line in output.split('\n'):
            port_match = re.match(r'^(\d+)/tcp\s+open', line)
            if port_match:
                port = int(port_match.group(1))
                open_ports.append(port)
        
        if not open_ports:
            return False, [], "未发现开放端口"
        
        print(f"  发现 {len(open_ports)} 个开放端口: {', '.join(str(p) for p in open_ports)}")
        
        # 过滤出可能的 SSL 端口（排除 80 等明确非 SSL 端口）
        ssl_ports = [p for p in open_ports if p != 80]
        
        if ssl_ports:
            return True, sorted(ssl_ports), f"发现 {len(ssl_ports)} 个可能的 SSL/HTTPS 端口"
        else:
            return False, [], "未发现 SSL/HTTPS 端口（只发现 HTTP 端口 80）"
            
    except subprocess.TimeoutExpired:
        return False, [], "端口扫描超时"
    except Exception as e:
        return False, [], f"端口扫描异常: {str(e)}"


def run_nmap_ssl_scan(ip: str, ports: list) -> tuple[bool, str, dict]:
    """
    使用 nmap 扫描目标的 SSL/TLS 协议支持情况
    
    Returns:
        (success, output, result_dict)
    """
    try:
        # 运行 nmap ssl-enum-ciphers 脚本
        port_str = ','.join(str(p) for p in ports)
        cmd = [
            'nmap', '--script', 'ssl-enum-ciphers',
            '-p', port_str, ip
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        
        output = result.stdout
        
        if result.returncode != 0 and not output:
            return False, f"nmap 执行失败: {result.stderr}", {}
        
        return True, output, {}
        
    except subprocess.TimeoutExpired:
        return False, f"nmap 扫描超时（{TIMEOUT}秒）", {}
    except FileNotFoundError:
        return False, "nmap 未安装", {}
    except Exception as e:
        return False, f"扫描异常: {str(e)}", {}


def parse_nmap_output(output: str) -> dict:
    """
    解析 nmap ssl-enum-ciphers 输出
    
    Returns:
        {
            port: {
                'protocols': {'insecure': [], 'secure': []},
                'insecure_ciphers': [],
                'warnings': [],
                'least_strength': ''
            }
        }
    """
    results = {}
    current_port = None
    current_protocol = None
    
    lines = output.split('\n')
    
    for i, line in enumerate(lines):
        # 检测端口行，如 "443/tcp open  https"
        port_match = re.match(r'^(\d+)/tcp\s+open', line)
        if port_match:
            current_port = int(port_match.group(1))
            results[current_port] = {
                'protocols': {'insecure': [], 'secure': []},
                'insecure_ciphers': [],
                'warnings': [],
                'least_strength': ''
            }
            continue
        
        if current_port is None:
            continue
        
        line_stripped = line.strip()
        
        # 检测协议版本行，如 "|   TLSv1.2:" 或 "|   SSLv3:"
        for proto in INSECURE_PROTOCOLS:
            if re.match(rf'^\|?\s*{proto}:', line_stripped, re.IGNORECASE):
                current_protocol = proto
                if proto not in results[current_port]['protocols']['insecure']:
                    results[current_port]['protocols']['insecure'].append(proto)
                break
        
        for proto in SECURE_PROTOCOLS:
            if re.match(rf'^\|?\s*{proto}:', line_stripped, re.IGNORECASE):
                current_protocol = proto
                if proto not in results[current_port]['protocols']['secure']:
                    results[current_port]['protocols']['secure'].append(proto)
                break
        
        # 检测不安全的加密套件
        for cipher in INSECURE_CIPHERS:
            if cipher.upper() in line.upper() and 'TLS_' in line.upper():
                # 提取加密套件名称
                cipher_match = re.search(r'(TLS_\S+)', line)
                if cipher_match:
                    cipher_name = cipher_match.group(1)
                    entry = f"{cipher_name} (端口 {current_port})"
                    if entry not in results[current_port]['insecure_ciphers']:
                        results[current_port]['insecure_ciphers'].append(entry)
        
        # 检测警告信息
        if 'warning' in line.lower() or any(w in line.lower() for w in ['vulnerable', 'deprecated', 'weak', 'broken']):
            if '|' in line and current_port:
                warning = line_stripped.lstrip('|').strip()
                if warning and warning not in results[current_port]['warnings']:
                    results[current_port]['warnings'].append(warning)
        
        # 检测最低强度
        if 'least strength' in line.lower():
            strength_match = re.search(r'least strength:\s*(\w)', line, re.IGNORECASE)
            if strength_match:
                results[current_port]['least_strength'] = strength_match.group(1)
    
    return results


def check_tls_security(ip: str, ports: list) -> tuple[bool, str, list, dict]:
    """
    检查 TLS 安全性
    
    Returns:
        (is_secure, output, issues_list, scan_results)
    """
    success, output, _ = run_nmap_ssl_scan(ip, ports)
    
    if not success:
        return None, output, [], {}
    
    scan_results = parse_nmap_output(output)
    issues = []
    
    if not scan_results:
        return None, "未检测到任何开放的 SSL/TLS 端口", [], {}
    
    for port, data in scan_results.items():
        # 检查不安全协议
        for proto in data['protocols']['insecure']:
            issues.append(f"端口 {port}: 支持不安全协议 {proto}")
        
        # 检查不安全加密套件
        for cipher in data['insecure_ciphers']:
            issues.append(f"端口 {port}: 使用不安全加密套件 {cipher.split(' (')[0]}")
        
        # 检查警告
        for warning in data['warnings']:
            if any(kw in warning.lower() for kw in ['3des', 'rc4', 'sweet32', 'deprecated', 'broken', 'weak']):
                issues.append(f"端口 {port}: {warning}")
        
        # 检查强度等级
        if data['least_strength'] in ['C', 'D', 'E', 'F']:
            issues.append(f"端口 {port}: 加密强度过低 (等级 {data['least_strength']})")
    
    # 去重
    issues = list(dict.fromkeys(issues))
    
    is_secure = len(issues) == 0
    
    return is_secure, output, issues, scan_results


def main():
    if len(sys.argv) < 2:
        print("用法: python check_tls_version.py <target_ip> [port1,port2,...|auto]")
        print("示例: python check_tls_version.py 192.168.1.1           # 自动发现端口")
        print("示例: python check_tls_version.py 192.168.1.1 443,8081  # 指定端口")
        print("示例: python check_tls_version.py 192.168.1.1 auto      # 显式自动发现")
        sys.exit(2)
    
    target_ip = sys.argv[1]
    
    print(f"目标: {target_ip}")
    print("=" * 60)
    
    # 解析端口参数
    if len(sys.argv) > 2 and sys.argv[2].lower() != 'auto':
        # 用户指定端口
        ports = [int(p.strip()) for p in sys.argv[2].split(',')]
        print(f"指定扫描端口: {', '.join(str(p) for p in ports)}")
    else:
        # 自动发现端口
        print("\n[步骤 1] 自动发现 SSL/HTTPS 端口...")
        success, discovered_ports, msg = discover_ssl_ports(target_ip)  # 不再需要 port_range 参数
        
        if success and discovered_ports:
            ports = discovered_ports
            print(f"  ✓ {msg}: {', '.join(str(p) for p in ports)}")
        else:
            print(f"  ⚠ {msg}，使用常见端口进行检测")
            ports = COMMON_HTTPS_PORTS
            print(f"  常见端口: {', '.join(str(p) for p in ports)}")
    
    print("\n[步骤 2] 检测 SSL/TLS 协议和加密套件...")
    print("（这可能需要一些时间）\n")
    
    is_secure, output, issues, scan_results = check_tls_security(target_ip, ports)
    
    if is_secure is None:
        print(f"✗ 扫描失败: {output}")
        print("\n" + "=" * 60)
        print("最终结果: ✗ 错误")
        sys.exit(2)
    
    # 显示扫描结果摘要
    print("扫描结果摘要:")
    print("-" * 40)
    
    for port, data in scan_results.items():
        print(f"\n端口 {port}:")
        
        # 显示协议
        all_protocols = data['protocols']['secure'] + data['protocols']['insecure']
        if all_protocols:
            print(f"  支持的协议: {', '.join(all_protocols)}")
            
            # 标记不安全协议
            if data['protocols']['insecure']:
                print(f"  ⚠ 不安全协议: {', '.join(data['protocols']['insecure'])}")
        
        # 显示不安全加密套件
        if data['insecure_ciphers']:
            print(f"  ⚠ 不安全加密套件:")
            for cipher in data['insecure_ciphers'][:5]:  # 最多显示5个
                print(f"    - {cipher.split(' (')[0]}")
            if len(data['insecure_ciphers']) > 5:
                print(f"    ... 还有 {len(data['insecure_ciphers']) - 5} 个")
        
        # 显示警告
        if data['warnings']:
            print(f"  ⚠ 安全警告:")
            for warning in data['warnings'][:3]:  # 最多显示3个
                print(f"    - {warning}")
        
        # 显示强度等级
        if data['least_strength']:
            strength_desc = {
                'A': '优秀', 'B': '良好', 'C': '较弱', 'D': '弱', 'E': '非常弱', 'F': '不安全'
            }
            desc = strength_desc.get(data['least_strength'], '未知')
            print(f"  最低加密强度: {data['least_strength']} ({desc})")
    
    print("\n" + "=" * 60)
    
    if is_secure:
        print("最终结果: ✓ 通过")
        print("说明: 目标只支持 TLS 1.2+ 安全协议，且无不安全加密组件")
        sys.exit(0)
    else:
        print("最终结果: ✗ 失败")
        print(f"\n发现 {len(issues)} 个安全问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
