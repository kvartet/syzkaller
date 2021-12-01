import re
import os
import argparse
import json
from typing import Any


struct_name, map_list = list(), list()


def parse_args() -> Any:
    parser = argparse.ArgumentParser(
        description='ucos descriptions wrapper converter')
    parser.add_argument('source_dir', type=str, default='ucos_', nargs='?',
                        help='the source dir')
    parser.add_argument('target_dir', type=str, default='ucos', nargs='?',
                        help='the target dir')
    parser.add_argument('mapping_file', type=str, default='mapping.h',
                        nargs='?', help='struct mapping file path')

    args = parser.parse_args()
    return args


def read_files(file_dir) -> list:
    file_list = list()
    for root, _, files in os.walk(file_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.txt':
                file_list.append(os.path.join(root, file))
    return file_list


def parse_file(path) -> str:
    text, res_set = str(), set()
    pattern = '(?P<func_name>[a-zA-Z\$_]*)\((?P<arg_name>[a-zA-Z_\*]*)\sptr\[(?P<ptr_dir>(in|out)),\s(?P<arg_type>[A-Z_\*]*)\](?P<remain>.*)'
    for line in open(path).readlines():
        if line.startswith('OS') or line.startswith('CPU') or line.startswith('Str') or \
                line.startswith('Math') or line.startswith('Mem') or line.startswith('res'):
            match = re.match(pattern, line)
            if match:
                match = match.groupdict()
                if match['arg_type'] == 'CPU_CHAR' or match['arg_type'] == 'void':
                    item = line
                else:
                    res = match['arg_type'].lower() + '_res'
                    res_set.add(res)
                    item = match['func_name'] + '(' + match['arg_name'] + ' ptr[' + \
                        match['ptr_dir'] + ', ' + res + ']' + match['remain']
                    map_list.append([match['func_name'], match['arg_type']])
            else:
                item = line
        else:
            item = line
        text = text + item if item.endswith('\n') else text + item + '\n'
    if len(res_set):
        for item in res_set:
            text = text + '\n' + 'resource ' + item + '[intptr]'
    return text


def write_file(path, text, write_type='w') -> None:
    write_type = 'w' if not os.path.exists(path) else write_type
    with open(path, write_type) as f:
        f.write(text)


def write_mapping(path) -> None:
    for item in map_list:
        write_file(path, '{"' + item[0] + '", ' + str(0) + ', "' + item[1] +
                   '", (struct_t)' + item[1] + '},\n', 'a+')

def convert_json(src, des):
    with open(src, 'r') as f:
        text = eval(f.read())
    mapping_dict = dict()
    for item in text:
        if item[0] in mapping_dict.keys():
            mapping_dict[item[0]].append([item[1], item[2]])
        else:
            mapping_dict[item[0]] = [[item[1], item[2]]]
    write_file(des, json.dumps(mapping_dict))

def extract_struct(path) -> None:
    pattern = '(?P<struct_name>[a-zA-Z_\$]*)\s*{'
    with open(path, 'r+') as f:
        text = f.read()
        match = re.findall(pattern, text)
        if len(match):
            struct_name.extend(match)


def main():
    args = parse_args()
    files = read_files(args.source_dir)
    for src in files:
        extract_struct(src)

    if not os.path.exists(args.target_dir):
        os.makedirs(args.target_dir)
    for src in files:
        text = parse_file(src)
        des = os.path.join(args.target_dir, os.path.basename(src))
        write_file(des, text)
    write_mapping(os.path.join(args.target_dir, args.mapping_file))



if __name__ == "__main__":
    # main()
    convert_json('ucos/mapping.h', 'mapping.json')
    # des = os.path.join(args.target_dir, os.path.basename(src))
    # write_file(des, text)
