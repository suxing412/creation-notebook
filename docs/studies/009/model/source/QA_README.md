# 009 数值门禁复跑

Blender 4.3.2，Python标准库；不需外部AI、账号/API或GPU。以下命令从解包根目录运行。先生成目标文件，再审它的实际字节；旧报告的PASS不能转移给重建文件。

```sh
blender -b --python-exit-code 1 --python source/audit_native.py -- --model assets/hinge/model.blend --glb assets/hinge/model.glb --info assets/hinge/model-info.json --report review/my-native.json
blender -b --python-exit-code 1 --python source/audit_assembly.py -- --model assets/hinge/model.blend --info assets/hinge/model-info.json --report review/my-assembly.json
blender -b --python-exit-code 1 --python source/audit_motion.py -- --model assets/hinge/model.blend --info assets/hinge/model-info.json --report review/my-motion.json --grid 3
```

运行CLI必须同时检查进程返回码、JSON `passed`、输入SHA和检查期间身份稳定性，不能仅找日志中的“PASS”字符串。

## 控制组

坏二进制只在运行后生成的work目录中；发行包不包含它们。普通几何控制是独立小型夹具，不冒充真实009模型；装配/运动控制才以实际发行HINGE构件为基线。每项必须命中自己指定的失败字段，而不是被任意其他问题拒绝就算通过。

```sh
blender -b --python-exit-code 1 --python source/audit_fault_controls.py -- --output work/qa-controls-final --report review/qa-controls-final.json
python source/audit_payload_controls.py
blender -b --python-exit-code 1 --python source/audit_assembly_controls.py
blender -b --python-exit-code 1 --python source/audit_contact_controls.py
```

以上会重新生成控制报告；需保留既有发行报告时，请在独立新解包副本运行。payload控制依赖第一条先生成的有效GLB；装配和metadata控制读取assets/hinge。因此不要跳过前置步骤后误称可复现失败。

## 非涵盖项

实际闭合mesh/字节/坐标三角多集相同，不等于索引拓扑同构、着色相同、实时不闪烁、真机可用或工程认证。运动格为有限角度采样，连续运动、任意参数组合、受力、线缆和防倾倒仍未验证。完整解释与真实检查器修正见 `../review/qa-method-and-failures.md`。

## 原发行身份复核

`python source/audit_verify_identity.py` 只验证原发行约定的assets三预设/六姿态及qa-final命名报告，不会自动收集上面的my-native等自选报告路径。新输出应另建与其实际文件绑定的报告集合，不能借原发行集合的PASS。
