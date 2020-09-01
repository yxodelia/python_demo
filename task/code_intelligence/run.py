import sys

sys.path.append('../..')

import json
import os
import re
import shutil
import subprocess
import tools.html_to_markdown as h2m
import tools.markdown_resolve as mr
from task.code_intelligence import crawl_data
from tools import file_size
from tools import file_compress
from collections import OrderedDict

# the version of every api doc
index_version = 7

tf_python_root_url = r'https://www.tensorflow.org/api_docs/python/'
keras_root_url = r'https://keras.io/'
pytorch_root_url = r'https://pytorch.org/docs/stable/'

encoding = r'utf-8'

# to run in different operation system, the path dose not contains slash or backslash
tf_python_dir = r'TensorFlow'
keras_dir = r'Keras'
pytorch_dir = r'PyTorch'

root_html_dir = r'tree_html'
root_md_dir = r'tree_md'

href_path_dict_list = dict()
href_path_dict_list[tf_python_dir] = OrderedDict()
href_path_dict_list[keras_dir] = OrderedDict()
href_path_dict_list[pytorch_dir] = OrderedDict()

crawl_data.crawl_tensor_flow_python_tree_structure(tf_python_root_url,
                                                   os.path.join(root_html_dir, tf_python_dir),
                                                   href_path_dict_list[tf_python_dir], encoding)
crawl_data.crawl_keras_tree_structure(keras_root_url, os.path.join(root_html_dir, keras_dir),
                                      href_path_dict_list[keras_dir], encoding)
crawl_data.crawl_pytorch_tree_structure(pytorch_root_url, os.path.join(root_html_dir, pytorch_dir),
                                        href_path_dict_list[pytorch_dir], encoding)

h2m.batch_html_to_markdown_save_source(root_html_dir, root_md_dir, '.html', '.md', 0, encoding)
mr.batch_latex_to_embedded_html(root_md_dir)

replace_reg = re.compile(r'.html$')
for index in href_path_dict_list:
    for i in href_path_dict_list[index]:
        # the reason of adding 2 is that there has the char '\'
        href_path_dict_list[index][i] = replace_reg.sub(r'.md', href_path_dict_list[index][i][
                                                                root_html_dir.__len__() + index.__len__() + 2:
                                                                href_path_dict_list[index][
                                                                    i].__len__()]).replace('\\', '/')
    open(os.path.join(root_md_dir, index, r'sidebar.json'), "w", encoding='utf-8').write(
        json.dumps(list(href_path_dict_list[index].values())))

href_path_dict_list[keras_dir][keras_root_url] = r'Home.md'

# get the root index.json file
json_read = open(r'index.json', 'r', encoding='utf-8', errors='ignore')
json_str = json_read.read()
index_dict = eval(json_str)

for framework_name in [keras_dir, pytorch_dir, tf_python_dir]:
    # convert the internal links
    mr.internal_links_convert(root_md_dir, framework_name, href_path_dict_list[framework_name],
                              encoding)

    # convert the internal links in every framework directory
    mr.batch_external_links_convert(os.path.join(root_md_dir, framework_name), encoding)

    # delete the hyperlink in title
    mr.batch_clean_title(os.path.join(root_md_dir, framework_name), encoding)

    # generate index.json file
    # run this script after editing all markdown texts
    shutil.copy(os.path.join(r'js_file', r'generate_index.js'),
                os.path.join(root_md_dir, framework_name, r'generate_index.js'))
    cmd = r'cd "' + os.path.join(root_md_dir, framework_name) + r'" && node generate_index.js'
    subprocess.call(cmd, shell=True)
    os.remove(os.path.join(root_md_dir, framework_name, r'generate_index.js'))

    # correct the size and version attribute of root index.json file
    index_dict[framework_name]['size'] = file_size.get_dirs_size(os.path.join(root_md_dir, framework_name))
    index_dict[framework_name]['version'] = index_version

    # package the directory
    file_compress.make_targz(os.path.join(root_md_dir, framework_name.lower() + r'.tar.gz'),
                             os.path.join(root_md_dir, framework_name))

    # save the change of root index.json file
open(os.path.join(r'js_file', r'index.json'), "w", encoding=encoding).write(json.dumps(index_dict))
