"""Self-contained GLB audit regressions. Only temporary fixtures are written.

Run: python -I tests/test_glb_audit.py (requires installed Node and Pillow).
The tiny compressed fixture is synthetic; no project models are copied.
"""
import base64
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lab/tools'))
import glb_audit as audit_module
import glb_audit_io as io
import build_assets as build


def pack(g, binary):
    encoded = json.dumps(g, separators=(',', ':')).encode(); encoded += b' ' * (-len(encoded) % 4)
    binary = bytes(binary) + b'\0' * (-len(binary) % 4)
    return struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary)) + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded + struct.pack('<II', len(binary), 0x004E4942) + binary


def triangle():
    binary = struct.pack('<9f3H', 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 2)
    g = {'asset': {'version': '2.0'}, 'buffers': [{'byteLength': len(binary)}],
         'bufferViews': [{'buffer': 0, 'byteLength': 36}, {'buffer': 0, 'byteOffset': 36, 'byteLength': 6}],
         'accessors': [{'bufferView': 0, 'componentType': 5126, 'type': 'VEC3', 'count': 3, 'min': [0,0,0], 'max': [1,1,0]}, {'bufferView': 1, 'componentType': 5123, 'type': 'SCALAR', 'count': 3}],
         'meshes': [{'primitives': [{'attributes': {'POSITION': 0}, 'indices': 1}]}], 'nodes': [{'mesh': 0}], 'scenes': [{'nodes': [0]}]}
    return g, binary


def compressed_triangle():
    fixture = json.loads((ROOT / 'tests/fixtures/triangle-meshopt.json').read_text())
    return pack(fixture['gltf'], base64.b64decode(fixture['binaryBase64']))


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='glb-audit-test-')
        self.path = Path(self.temp.name) / 'fixture.glb'
    def tearDown(self): self.temp.cleanup()
    def audit(self, raw):
        self.path.write_bytes(raw); result = audit_module.audit(self.path)
        self.assertEqual(result['bytes'], len(raw)); self.assertEqual(result['sha256'], hashlib.sha256(raw).hexdigest())
        return result
    def reject(self, raw, code=None):
        result = self.audit(raw); self.assertTrue(result['fatalErrors'], result)
        if code: self.assertIn(code, result['fatalErrors'][0])
    def test_raw_stats_and_hygiene(self):
        result = self.audit(pack(*triangle()))
        self.assertFalse(result['fatalErrors']); self.assertEqual(result['triangles'], 1)
        self.assertEqual(result['size'], [1.0,1.0,0.0]); self.assertIn('PRIMS_NO_NORMAL:1', result['issues'])
    def test_compressed_stats_and_byte_identity(self):
        result = self.audit(compressed_triangle())
        self.assertFalse(result['fatalErrors']); self.assertEqual(result['triangles'], 1)
        self.assertEqual(result['decodedViews'],2); self.assertEqual(result['images'],0)
    def test_header_failures(self):
        raw = pack(*triangle())
        variants = [b'', b'glTF', raw[:19], b'nope'+raw[4:], raw[:4]+struct.pack('<I',1)+raw[8:], raw[:-1], raw+b'x', raw[:12]+struct.pack('<I',999999)+raw[16:]]
        for raw in variants:
            with self.subTest(size=len(raw)): self.reject(raw)
    def test_layout_failures(self):
        def make(case):
            g,b = triangle(); case(g); return pack(g,b)
        cases = [lambda g: g['buffers'][0].update(uri='https://example.invalid/file.bin'),
                 lambda g: g['buffers'][0].update(byteLength=4),
                 lambda g: g['bufferViews'][0].update(byteLength=400),
                 lambda g: g['bufferViews'][0].update(buffer=1),
                 lambda g: g['bufferViews'][0].update(byteOffset=-1),
                 lambda g: g['bufferViews'][0].update(byteStride=1),
                 lambda g: g['accessors'][0].update(count=4),
                 lambda g: g['accessors'][0].update(count=10**12),
                 lambda g: g['accessors'][0].update(byteOffset=2),
                 lambda g: g['accessors'][0].update(sparse={}),
                 lambda g: g['accessors'][0].update(bufferView=99),
                 lambda g: g['accessors'][1].update(componentType=5126),
                 lambda g: g['nodes'][0].update(children=[0]),
                 lambda g: g['nodes'][0].update(mesh=100),
                 lambda g: g['scenes'][0].update(nodes=[100]),
                 lambda g: g.update(images=[{'uri':'data:image/png;base64,AAAA'}])]
        for case in cases:
            with self.subTest(case=case): self.reject(make(case))
    def test_invalid_repeated_indices_rejected_before_degeneracy(self):
        g,b = triangle(); b=b[:36]+struct.pack('<3H',9,9,9); self.reject(pack(g,b),'INDEX_OUT_OF_RANGE')
    def test_nonfinite_geometry_rejected(self):
        g,b=triangle(); self.reject(pack(g,struct.pack('<f',float('nan'))+b[4:]),'NONFINITE_ACCESSOR_DATA')
    def test_minmax_lies_rejected(self):
        g,b=triangle();g['accessors'][0]['max']=[0,0,0]; self.reject(pack(g,b),'POSITION_OUTSIDE_MINMAX')
    def test_required_unknown_reject_optional_metadata_accept(self):
        g,b=triangle();g.update(extensionsUsed=['KHR_materials_emissive_strength']); self.assertFalse(self.audit(pack(g,b))['fatalErrors'])
        g['extensionsRequired']=['KHR_materials_emissive_strength'];self.reject(pack(g,b),'EXT_REQUIRED_UNSUPPORTED')
    def test_quantized_required_extension_explicitly_unsupported(self):
        g,b=triangle();g.update(extensionsUsed=['KHR_mesh_quantization'],extensionsRequired=['KHR_mesh_quantization'])
        self.reject(pack(g,b),'EXT_REQUIRED_UNSUPPORTED')
    def test_normalized_attribute_reader(self):
        g,b=triangle();g['bufferViews'].append({'buffer':0,'byteOffset':44,'byteLength':4})
        g['accessors'].append({'bufferView':2,'componentType':5121,'type':'VEC4','count':1,'normalized':True})
        b=b+b'\0\0'+bytes([0,255,128,0]);g['buffers'][0]['byteLength']=len(b)
        g,b=io.load_glb(pack(g,b));data=io.Accessors(g,b)
        self.assertEqual(data.read(2)[0],(0.0,1.0,128/255,0.0))
    def test_compressed_metadata_failures(self):
        source,b=io.load_glb(compressed_triangle())
        cases=[('buffer',1),('byteOffset',10**9),('byteLength',10**9),('byteStride',7),('count',10**12),('mode','UNKNOWN'),('filter','UNKNOWN')]
        for key,value in cases:
            g=copy.deepcopy(source);g['bufferViews'][0]['extensions'][io.EXT][key]=value
            with self.subTest(key=key): self.reject(pack(g,b))
        g=copy.deepcopy(source);g['buffers'][1]['extensions'][io.EXT]['fallback']='false';self.reject(pack(g,b),'INVALID_FALLBACK_FLAG')
        g=copy.deepcopy(source);g['bufferViews'][0].pop('extensions');self.reject(pack(g,b),'UNBACKED_VIEW')
    def test_corrupted_stream_rejects(self):
        g,b=io.load_glb(compressed_triangle());b=bytearray(b);b[g['bufferViews'][0]['extensions'][io.EXT]['byteOffset']]=0;self.reject(pack(g,b),'MESHOPT_DECODE_FAILED')
    def test_missing_node_and_decoder(self):
        with patch.object(io.shutil,'which',return_value=None): self.reject(compressed_triangle(),'MESHOPT_NODE_MISSING')
        with patch.object(io,'DECODER',Path(self.temp.name)/'absent'): self.reject(compressed_triangle(),'MESHOPT_DECODER_MISSING')
    def test_decoder_process_failure_timeout_and_length(self):
        for result in [subprocess.CompletedProcess([],1,b'',b'failed'),subprocess.CompletedProcess([],0,b'x',b'')]:
            with patch.object(io.subprocess,'run',return_value=result): self.reject(compressed_triangle())
        with patch.object(io.subprocess,'run',side_effect=subprocess.TimeoutExpired('node',30)):
            self.reject(compressed_triangle(),'MESHOPT_TIMEOUT')
    def test_cache_same_size_same_second_mutation(self):
        g,b=triangle();self.path.write_bytes(pack(g,b));stamp=self.path.stat()
        with patch.object(build,'DOCS',self.temp.name),patch.object(build,'cache',{}):
            self.assertEqual(build.glb_info('fixture.glb')['triangles'],1)
            self.path.write_bytes(pack(g,b[:36]+struct.pack('<3H',9,9,9)))
            os.utime(self.path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
            self.assertEqual(self.path.stat().st_size,stamp.st_size)
            with self.assertRaisesRegex(ValueError,'INDEX_OUT_OF_RANGE'): build.glb_info('fixture.glb')
    def test_cache_warm_compressed_cannot_hide_missing_decoder(self):
        self.path.write_bytes(compressed_triangle())
        with patch.object(build,'DOCS',self.temp.name),patch.object(build,'cache',{}):
            self.assertEqual(build.glb_info('fixture.glb')['triangles'],1)
            with patch.object(io.shutil,'which',return_value=None):
                with self.assertRaisesRegex(ValueError,'MESHOPT_NODE_MISSING'):build.glb_info('fixture.glb')
    def test_cache_corruption_reaudits(self):
        self.path.write_bytes(pack(*triangle()))
        with patch.object(build,'DOCS',self.temp.name),patch.object(build,'cache',{}):
            build.glb_info('fixture.glb');key=next(iter(build.cache))
            for invalid in ({'extUsed':[]},{'auditIdentity':build.AUDIT_ID,'summary':{}},True):
                build.cache[key]=invalid
                with patch.object(build,'audit',wraps=build.audit) as spy:
                    self.assertEqual(build.glb_info('fixture.glb')['triangles'],1);self.assertEqual(spy.call_count,1)
    def test_cache_cannot_lie_about_current_compression(self):
        self.path.write_bytes(compressed_triangle())
        with patch.object(build,'DOCS',self.temp.name),patch.object(build,'cache',{}):
            build.glb_info('fixture.glb');key=next(iter(build.cache));build.cache[key]['summary']['extUsed']=[]
            with patch.object(io.shutil,'which',return_value=None):
                with self.assertRaisesRegex(ValueError,'MESHOPT_NODE_MISSING'):build.glb_info('fixture.glb')
    def test_cache_identity_binds_decoder(self):
        before=io.cache_identity();fake=Path(self.temp.name)/'decoder.js';fake.write_bytes(b'// changed')
        with patch.object(io,'DECODER',fake):self.assertNotEqual(before,io.cache_identity())
    def test_reverse_order_deep_graph_rejected(self):
        g,b=triangle();g['nodes']=[{'mesh':0}]+[{'children':[i-1]} for i in range(1,140)];g['scenes']=[{'nodes':[139]}]
        self.reject(pack(g,b),'NODE_DEPTH_LIMIT')
    def test_corrupt_cache_file_rebuilt_by_official_checker(self):
        # Run the actual entrypoint in an isolated empty-library fixture; the
        # corrupt hint must not abort before report generation.
        fixture=Path(self.temp.name)/'cache-fixture';(fixture/'lab/data').mkdir(parents=True)
        shutil.copytree(ROOT/'lab/tools',fixture/'lab/tools',ignore=shutil.ignore_patterns('__pycache__'))
        (fixture/'docs/asset-spec').mkdir(parents=True)
        shutil.copyfile(ROOT/'docs/asset-spec/categories.json',fixture/'docs/asset-spec/categories.json')
        (fixture/'lab/data/glb-cache.json').write_text('{broken')
        run=subprocess.run([sys.executable,'-I','lab/tools/build_assets.py','--check'],cwd=fixture,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(json.loads((fixture/'lab/data/report.json').read_text())['counts']['withErrors'],0)
        self.assertEqual(json.loads((fixture/'lab/data/glb-cache.json').read_text()),{})
    def test_isolated_mode_cli_reports_and_exit_codes(self):
        listfile=Path(self.temp.name)/'files.txt';listfile.write_text('fixture.glb\n')
        report=Path(self.temp.name)/'result.json'
        for raw,expected in [(pack(*triangle()),0),(b'bad',1),(compressed_triangle(),0)]:
            self.path.write_bytes(raw)
            run=subprocess.run([sys.executable,'-I',str(ROOT/'lab/tools/glb_audit.py'),self.temp.name,str(listfile),str(report)],capture_output=True,text=True)
            self.assertEqual(run.returncode,expected,run.stdout+run.stderr)
            result=json.loads(report.read_text())[0];self.assertEqual(result['sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(bool(result['fatalErrors']),expected==1)
    def test_late_failure_has_no_completed_geometry_metrics(self):
        g,b=triangle();del g['accessors'][0]['max']
        broken=[pack(g,b)]
        g,b=triangle();g['nodes']=[{'scale':[1e308,1e308,1e308],'children':[1]},{'mesh':0,'scale':[1e308,1e308,1e308]}]
        broken.append(pack(g,b))
        for raw in broken:
            result=self.audit(raw);self.assertTrue(result['fatalErrors'])
            for field in ['triangles','vertices','degenerateTris','bboxMin','decodedViews']:
                self.assertNotIn(field,result)
    def test_preallocation_limit(self):
        g,b=io.load_glb(compressed_triangle());g['buffers'][1]['byteLength']=10**12
        with patch.object(io.subprocess,'run',side_effect=AssertionError('decoder must not run')):
            self.reject(pack(g,b),'INVALID_BUFFER_LENGTH')


    def test_placeholder_marker_is_optional(self):
        source,b = io.load_glb(compressed_triangle())
        for marker in (None, False, True):
            g=copy.deepcopy(source)
            if marker is None: g['buffers'][1].pop('extensions')
            else: g['buffers'][1]['extensions'][io.EXT]['fallback']=marker
            result=self.audit(pack(g,b)); self.assertFalse(result['fatalErrors'],result)
            self.assertEqual(result['triangles'],1); self.assertEqual(result['decodedViews'],2)
        g=copy.deepcopy(source);g['buffers'][0]['extensions']={io.EXT:{'fallback':True}}
        self.reject(pack(g,b),'FALLBACK_SOURCE_REFERENCE')
        g,b=triangle();g['buffers'][0]['extensions']={io.EXT:{'fallback':True}}
        self.reject(pack(g,b),'FALLBACK_RAW_REFERENCE')

    def test_integer_notations_and_invalid_numbers(self):
        # JSON reserialization must not round a fractional token into an integer.
        for encoded in ('3','3.0','3e0'):
            g,b=triangle();g['accessors'][0]['count']='COUNT'
            raw=pack(g,b);j,bb=io.load_glb(raw)
            text=json.dumps(j).replace('"COUNT"',encoded).encode();text+=b' '*(-len(text)%4)
            raw=struct.pack('<4sII',b'glTF',2,28+len(text)+len(bb))+struct.pack('<II',len(text),0x4E4F534A)+text+struct.pack('<II',len(bb),0x004E4942)+bb
            self.assertFalse(self.audit(raw)['fatalErrors'])
        g,b=triangle();g['nodes'][0]['mesh']=0.0;g['accessors'][0]['bufferView']=0.0
        g['bufferViews'][0]['byteOffset']=0.0;self.assertFalse(self.audit(pack(g,b))['fatalErrors'])
        g,b=io.load_glb(compressed_triangle());g['bufferViews'][0]['extensions'][io.EXT]['count']=3.0
        self.assertFalse(self.audit(pack(g,b))['fatalErrors'])
        for count in (True,3.5,float('inf')):
            g,b=triangle();g['accessors'][0]['count']=count;self.reject(pack(g,b))
        self.assertIs(type(io.json_number('3.0000000000000001')),float)
        self.assertIs(type(io.json_number('1e-999')),float)
        with self.assertRaises(io.AuditError):io.integer(io.json_number('1e-999'),'fraction')

    def test_extreme_decimal_exponent_is_reported(self):
        g,b=triangle();g['accessors'][0]['count']='EXPONENT'
        data=json.dumps(g).replace('"EXPONENT"','1e-9999999999999999999').encode()
        data+=b' '*(-len(data)%4);binary=b+b'\0'*(-len(b)%4)
        raw=struct.pack('<4sII',b'glTF',2,28+len(data)+len(binary))+struct.pack('<II',len(data),0x4E4F534A)+data+struct.pack('<II',len(binary),0x004E4942)+binary
        result=self.audit(raw);self.assertIn('INVALID_JSON_NUMBER',result['fatalErrors'][0])
        self.assertNotIn('triangles',result)

    def test_matrix_last_column_padding_and_alignment(self):
        for kind,ctype,cs,stride,span in [('MAT2',5121,1,8,6),('MAT3',5121,1,12,11),('MAT3',5123,2,24,22)]:
            for count in (1,2):
                length=stride*(count-1)+span
                g={'asset':{'version':'2.0'},'buffers':[{'byteLength':length}],
                   'bufferViews':[{'buffer':0,'byteLength':length}],
                   'accessors':[{'bufferView':0,'componentType':ctype,'type':kind,'count':count}]}
                raw=pack(g,bytes(length));data=io.Accessors(*io.load_glb(raw))
                self.assertEqual(len(data.read(0)),count)
                self.assertTrue(all(x==0 for row in data.read(0) for x in row))
                g['bufferViews'][0]['byteLength']-=1;self.reject(pack(g,bytes(length)),'ACCESSOR_OUT_OF_BOUNDS')
                g['bufferViews'][0]['byteLength']=length+4;g['buffers'][0]['byteLength']=length+4
                g['accessors'][0]['byteOffset']=cs
                self.reject(pack(g,bytes(length+4)),'INVALID_MATRIX_ALIGNMENT')

    def test_world_bounds_are_finite_or_fail_without_stats(self):
        g,b=triangle();g['nodes'][0]['translation']=[1e308,0,0]
        result=self.audit(pack(g,b));self.assertFalse(result['fatalErrors'])
        self.assertEqual(result['center'][0],1e308)
        json.dumps(result,allow_nan=False)
        g['nodes'].append({'mesh':0,'translation':[-1e308,0,0]});g['scenes'][0]['nodes']=[0,1]
        result=self.audit(pack(g,b));self.assertIn('NONFINITE_WORLD_BOUNDS',result['fatalErrors'][0])
        self.assertNotIn('triangles',result);self.assertNotIn('size',result)

    def test_raw_cache_hit_and_structural_damage(self):
        raw=pack(*triangle());self.path.write_bytes(raw)
        with patch.object(build,'DOCS',self.temp.name),patch.object(build,'cache',{}):
            expected=copy.deepcopy(build.glb_info('fixture.glb'));key=next(iter(build.cache));good=copy.deepcopy(build.cache[key])
            with patch.object(build,'audit',side_effect=AssertionError('valid raw cache should hit')):
                self.assertEqual(build.glb_info('fixture.glb'),expected)
            mutations=[lambda x:x.update(auditIdentity='old'),lambda x:x['summary'].pop('size'),
                       lambda x:x['summary'].update(triangles=-1),lambda x:x['summary'].update(triangles=True),
                       lambda x:x['summary'].update(size=[float('nan'),1,0]),lambda x:x['summary'].update(issues=['PARSE_ERROR:bad'])]
            for mutate in mutations:
                damaged=copy.deepcopy(good);mutate(damaged);build.cache[key]=damaged
                with patch.object(build,'audit',wraps=build.audit) as spy:
                    self.assertEqual(build.glb_info('fixture.glb'),expected);self.assertEqual(spy.call_count,1)

    def test_failed_compressed_refresh_removes_success_entry(self):
        self.path.write_bytes(compressed_triangle())
        with patch.object(build,'DOCS',self.temp.name),patch.object(build,'cache',{}):
            build.glb_info('fixture.glb');key=next(iter(build.cache))
            with patch.object(io.shutil,'which',return_value=None):
                with self.assertRaisesRegex(ValueError,'MESHOPT_NODE_MISSING'):build.glb_info('fixture.glb')
            self.assertNotIn(key,build.cache)

    def test_fingerprint_sources_and_raw_without_node(self):
        before=io.cache_identity()
        for attr in ('DECODER','BRIDGE'):
            fake=Path(self.temp.name)/(attr+'.js');fake.write_text('// different implementation')
            with patch.object(io,attr,fake):self.assertNotEqual(before,io.cache_identity())
        with patch.object(io,'AUDIT_SCHEMA','new-contract'):self.assertNotEqual(before,io.cache_identity())
        with patch.object(io.shutil,'which',return_value=None):
            self.assertFalse(self.audit(pack(*triangle()))['fatalErrors'])

    def fixture_repository(self):
        root=Path(self.temp.name)/'isolated-repository';(root/'lab/data').mkdir(parents=True)
        shutil.copytree(ROOT/'lab/tools',root/'lab/tools',ignore=shutil.ignore_patterns('__pycache__'))
        for rel in ('docs/asset-spec/categories.json','docs/vendor/meshopt_decoder.module.js'):
            dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
        carddir=root/'docs/library/models/m-audit-test';carddir.mkdir(parents=True)
        from PIL import Image
        Image.new('RGB',(800,600),(200,200,200)).save(carddir/'cover.webp')
        (carddir/'triangle.glb').write_bytes(compressed_triangle())
        card={'spec':1,'id':'m-audit-test','category':'models','kind':'城市构件','title':'Synthetic triangle',
              'summary':'Temporary audit test fixture.','status':'草稿','cover':'cover.webp','files':[{'path':'triangle.glb'}]}
        (carddir/'m-audit-test.asset.json').write_text(json.dumps(card,ensure_ascii=False))
        return root

    def test_actual_checker_cold_warm_corrupt_and_missing_decoder(self):
        root=self.fixture_repository();command=[sys.executable,'-I','lab/tools/build_assets.py','--check']
        def check(code):
            run=subprocess.run(command,cwd=root,capture_output=True,text=True)
            self.assertEqual(run.returncode,code,run.stdout+run.stderr)
            report=json.loads((root/'lab/data/report.json').read_text())
            self.assertEqual(report['counts']['withErrors'],code)
            return json.loads((root/'lab/data/glb-cache.json').read_text())
        for _ in range(2):
            cache=check(0);self.assertEqual(len(cache),1)
            self.assertEqual(next(iter(cache.values()))['summary']['triangles'],1)
        (root/'lab/data/glb-cache.json').write_text('{broken');check(0)
        decoder=root/'docs/vendor/meshopt_decoder.module.js';saved=decoder.read_bytes();decoder.unlink()
        cache=check(1)
        decoder.write_bytes(saved)
        model=root/'docs/library/models/m-audit-test/triangle.glb';g,b=io.load_glb(model.read_bytes());bad=bytearray(b);bad[0]=0
        model.write_bytes(pack(g,bad));check(1)
        text=(root/'lab/data/report.json').read_text();self.assertIn('MESHOPT_DECODE_FAILED',text)

    def test_real_decoder_timeout_uses_only_temporary_bridge(self):
        bridge=Path(self.temp.name)/'timeout.mjs';bridge.write_text('setTimeout(() => {}, 60000);')
        start=time.monotonic()
        with patch.object(io,'BRIDGE',bridge):self.reject(compressed_triangle(),'MESHOPT_TIMEOUT')
        elapsed=time.monotonic()-start
        self.assertGreaterEqual(elapsed,29);self.assertLess(elapsed,40)

    def test_child_drops_node_preload_environment(self):
        actual=io.subprocess.run
        def invoke(*args,**kwargs):
            self.assertNotIn('NODE_OPTIONS',kwargs['env']);self.assertNotIn('NODE_PATH',kwargs['env'])
            return actual(*args,**kwargs)
        with patch.dict(os.environ,{'NODE_OPTIONS':'--require=/nonexistent/preload','NODE_PATH':'/nonexistent/modules'}),patch.object(io.subprocess,'run',side_effect=invoke):
            self.assertFalse(self.audit(compressed_triangle())['fatalErrors'])

if __name__=='__main__':unittest.main(verbosity=2)
