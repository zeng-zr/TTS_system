#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import argparse
import os

def remove_line_numbers(input_file, output_file=None):
    """
    去除文本文件每行句首的序号数字
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径，如果不提供则覆盖原文件
    """
    # 如果未提供输出文件，则覆盖原文件
    if output_file is None:
        output_file = input_file
        
    # 临时文件路径
    temp_file = output_file + '.tmp'
    
    # 读取输入文件并处理每一行
    with open(input_file, 'r', encoding='utf-8') as f_in, open(temp_file, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            # 使用正则表达式去除行首的序号数字（可能带有引号或其他符号）
            # 匹配模式：行首的数字序列，可能后面跟着引号或其他标点符号
            processed_line = re.sub(r'^\d+["\']?\s*', '', line)
            f_out.write(processed_line)
    
    # 替换原文件
    os.replace(temp_file, output_file)
    print(f"已处理文件：{input_file}")
    if output_file != input_file:
        print(f"结果已保存至：{output_file}")

if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='去除文本文件每行句首的序号数字')
    parser.add_argument('input_file', help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（可选，默认覆盖原文件）')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"错误：文件 '{args.input_file}' 不存在")
        exit(1)
    
    # 执行处理
    remove_line_numbers(args.input_file, args.output)