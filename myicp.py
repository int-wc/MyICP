import requests
from bs4 import BeautifulSoup
import re
import time
import csv
import argparse

def print_banner():
    print(r"""
MMMMMMMM               MMMMMMMM                     IIIIIIIIII     CCCCCCCCCCCCPPPPPPPPPPPPPPPPP   
M:::::::M             M:::::::M                     I::::::::I  CCC::::::::::::P::::::::::::::::P  
M::::::::M           M::::::::M                     I::::::::ICC:::::::::::::::P::::::PPPPPP:::::P 
M:::::::::M         M:::::::::M                     II::::::IC:::::CCCCCCCC::::PP:::::P     P:::::P
M::::::::::M       M::::::::::yyyyyyy           yyyyyyI::::IC:::::C       CCCCCC P::::P     P:::::P
M:::::::::::M     M:::::::::::My:::::y         y:::::yI::::C:::::C               P::::P     P:::::P
M:::::::M::::M   M::::M:::::::M y:::::y       y:::::y I::::C:::::C               P::::PPPPPP:::::P 
M::::::M M::::M M::::M M::::::M  y:::::y     y:::::y  I::::C:::::C               P:::::::::::::PP  
M::::::M  M::::M::::M  M::::::M   y:::::y   y:::::y   I::::C:::::C               P::::PPPPPPPPP    
M::::::M   M:::::::M   M::::::M    y:::::y y:::::y    I::::C:::::C               P::::P            
M::::::M    M:::::M    M::::::M     y:::::y:::::y     I::::C:::::C               P::::P            
M::::::M     MMMMM     M::::::M      y:::::::::y      I::::IC:::::C       CCCCCC P::::P            
M::::::M               M::::::M       y:::::::y     II::::::IC:::::CCCCCCCC::::PP::::::PP          
M::::::M               M::::::M        y:::::y      I::::::::ICC:::::::::::::::P::::::::P          
M::::::M               M::::::M       y:::::y       I::::::::I  CCC::::::::::::P::::::::P          
MMMMMMMM               MMMMMMMM      y:::::y        IIIIIIIIII     CCCCCCCCCCCCPPPPPPPPPP          
                                    y:::::y                                                         
                                   y:::::y                                                          
                                  y:::::y                                                          
                                 y:::::y                                                           
                                yyyyyyy                                                            
    """)
    print("Author: weichai")


# 从文件中读取所有域名或路径
def get_domains_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]  # 读取所有行并去除两边空白字符

# 检测是否是IP地址
def is_ip_address(domain):
    # 正则表达式匹配IPv4地址
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    return bool(ip_pattern.match(domain))

# 解析命令行参数
def parse_arguments():
    parser = argparse.ArgumentParser(description='从文件中提取域名并对icp.chinaz.com发起请求。')
    parser.add_argument('--user-agent', type=str, required=True, help='指定User-Agent')
    parser.add_argument('--cookie', type=str, required=True, help='指定Cookie')
    parser.add_argument('--file', type=str, required=True, help='指定包含域名或路径的文件')
    parser.add_argument('--output', type=str, required=True, help='指定输出的CSV文件路径')
    return parser.parse_args()

# 主函数
def main():
    print_banner()  # 打印字符画和作者信息
    
    args = parse_arguments()
    
    if not args.user_agent or not args.cookie:
        print('错误: 必须提供User-Agent和Cookie参数。')
        print('使用示例:')
        print('python script.py --user-agent "your-user-agent" --cookie "your-cookie" --file target.txt --output output.csv')
        return

    headers = {
        'Host': 'icp.chinaz.com',
        'User-Agent': args.user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Connection': 'keep-alive',
        'Cookie': args.cookie,
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Priority': 'u=0, i'
    }

    # 从文件提取所有域名
    domains = get_domains_from_file(args.file)

    # 打开CSV文件准备写入结果
    with open(args.output, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Domain', 'Company Name', 'HTTP Response Time (s)', 'Parse Time (s)'])  # 写入CSV标题行
        
        for domain in domains:
            if is_ip_address(domain):
                print(f'{domain} - 检测到IP地址，跳过')
                continue
            
            # 构建完整的URL，并动态更新路径
            full_url = f'https://icp.chinaz.com/{domain}'
            
            # 发起GET请求
            try:
                start_request_time = time.time()  # 记录请求开始时间
                response = requests.get(full_url, headers=headers, timeout=10)  # 设置超时时间为10秒
                response.raise_for_status()  # 检查请求是否成功
                response_time = time.time() - start_request_time  # 计算请求的响应时间
                
                # 解析HTML
                start_parse_time = time.time()  # 记录开始解析主办单位名称的时间
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找主办单位名称后的内容
                label = soup.find('td', text='主办单位名称')
                if label:
                    # 获取下一个兄弟元素
                    company_info = label.find_next_sibling('td').find('a').text.strip()
                    parse_time = time.time() - start_parse_time  # 计算解析主办单位名称的时间
                    print(f'{domain} - 主办单位名称: {company_info} (HTTP响应时间: {response_time:.2f}秒 | 解析时间: {parse_time:.2f}秒)')
                    
                    # 将结果写入CSV
                    writer.writerow([domain, company_info, f'{response_time:.2f}', f'{parse_time:.2f}'])
                else:
                    print(f'{domain} - 未找到主办单位名称信息')
                    writer.writerow([domain, '未找到主办单位名称', f'{response_time:.2f}', 'N/A'])
                    
            except requests.exceptions.Timeout:
                print(f'{domain} - 请求超时，已放弃')
                writer.writerow([domain, '请求超时', '超时', 'N/A'])
            except requests.RequestException as e:
                print(f'{domain} - 请求失败: {e}')
                writer.writerow([domain, '请求失败', '失败', 'N/A'])

    print(f'结果已导出至 {args.output}')

if __name__ == '__main__':
    main()
