# -*- coding: utf-8 -*-
"""在冻结库副本上跑库自带的反例测试 test_checks.py（库与测试脚本不改字节；只把贴图目录改指本席位 textures/）。
用法: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P source/run_lib_tests.py -- <LY-007 目录> <outdir>
"""
import sys, os, runpy
argv = sys.argv[sys.argv.index('--') + 1:]
W = os.path.abspath(argv[0]); OUT = os.path.abspath(argv[1])
LIB = os.path.join(W, 'source', 'lib'); sys.path.insert(0, LIB)
import ly_style as ly  # noqa: E402
ly.TEX_DIR = os.path.join(W, 'textures')
sys.argv = [os.path.join(LIB, 'test_checks.py'), '--', OUT]
runpy.run_path(os.path.join(LIB, 'test_checks.py'), run_name='__main__')
