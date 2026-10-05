"""Independent original measurement adapter; never a native-port dependency.

Requires the separately compiled, ignored SameBoy 1.0.3 reference library and
its open-source DMG boot ROM. Provides buttons, read-only measurements and
unmodified save/load states. No emulator core source is included here.
"""
import ctypes
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
REFERENCE_ROOT=ROOT/'.tools/sameboy-reference'
REVISION='208ba4afabffab9edde416f2dbb8ae459e34adb8'
BOOT=ROOT/'.tools/sameboy-windows-reference/dmg_boot.bin'
BUILD=json.loads((REFERENCE_ROOT/'reference-build.json').read_text())
if BUILD.get('version')!='1.0.3' or BUILD.get('sourceRevision')!=REVISION or not BUILD.get('referenceOnly'):
    raise RuntimeError('Build the pinned reference adapter with tools/build_sameboy_reference.py')
if hashlib.sha256((REFERENCE_ROOT/'reference-adapter.dll').read_bytes()).hexdigest()!=BUILD['dllSha256']:
    raise RuntimeError('Reference DLL differs from its build manifest')
if hashlib.sha256(BOOT.read_bytes()).hexdigest()!='6f64da4cecd7e54e2f928eb3e3ba7810a7a567d0d247cc71737d1771e073a916':
    raise RuntimeError('Requires the official SameBoy 1.0.3 open-source DMG boot ROM')
DLL=ctypes.CDLL(str(REFERENCE_ROOT/'reference-adapter.dll'))
DLL.ref_version.restype=ctypes.c_char_p
if DLL.ref_version()!=b'1.0.3':raise RuntimeError('Reference DLL must be built from SameBoy 1.0.3')
PTR=ctypes.c_void_p
HOOK=ctypes.CFUNCTYPE(None,PTR,ctypes.c_uint,ctypes.c_uint,ctypes.c_uint64)
DLL.ref_open.argtypes=[ctypes.c_char_p,ctypes.c_char_p];DLL.ref_open.restype=PTR
DLL.ref_model.argtypes=[PTR];DLL.ref_model.restype=ctypes.c_uint
for name in ('ref_close','ref_fail'):
    getattr(DLL,name).argtypes=[PTR]
DLL.ref_hook.argtypes=[PTR,HOOK]
DLL.ref_watch.argtypes=[PTR,ctypes.c_uint]
DLL.ref_tick.argtypes=[PTR,ctypes.c_uint]
DLL.ref_peek.argtypes=[PTR,ctypes.c_uint];DLL.ref_peek.restype=ctypes.c_uint8
DLL.ref_reg.argtypes=[PTR,ctypes.c_uint];DLL.ref_reg.restype=ctypes.c_uint
DLL.ref_key.argtypes=[PTR,ctypes.c_uint,ctypes.c_int]
DLL.ref_cycles.argtypes=[PTR];DLL.ref_cycles.restype=ctypes.c_uint64
DLL.ref_pixels.argtypes=[PTR];DLL.ref_pixels.restype=PTR
DLL.ref_save.argtypes=[PTR,ctypes.c_char_p];DLL.ref_save.restype=ctypes.c_int
DLL.ref_load.argtypes=[PTR,ctypes.c_char_p];DLL.ref_load.restype=ctypes.c_int
KEYS={'right':0,'left':1,'up':2,'down':3,'a':4,'b':5,'select':6,'start':7}

class Memory:
    def __init__(self,p):self.p=p
    def __getitem__(self,address):
        if isinstance(address,slice):return [self[i] for i in range(*address.indices(65536))]
        if not 0<=address<65536:raise ValueError('Invalid reference address')
        return DLL.ref_peek(self.p.handle,address)

class Registers:
    def __init__(self,p):self.p=p
    @property
    def SP(self):return DLL.ref_reg(self.p.handle,4)
    @property
    def PC(self):return DLL.ref_reg(self.p.handle,5)
    @property
    def F(self):return DLL.ref_reg(self.p.handle,0)&255
    @property
    def A(self):return DLL.ref_reg(self.p.handle,0)>>8
    @property
    def B(self):return DLL.ref_reg(self.p.handle,1)>>8
    @property
    def C(self):return DLL.ref_reg(self.p.handle,1)&255
    @property
    def D(self):return DLL.ref_reg(self.p.handle,2)>>8
    @property
    def E(self):return DLL.ref_reg(self.p.handle,2)&255

class Screen:
    def __init__(self,p):self.p=p
    @property
    def image(self):
        values=(ctypes.c_uint32*(160*144)).from_address(DLL.ref_pixels(self.p.handle))
        pixels=bytes(channel for value in values for channel in ((value>>16)&255,(value>>8)&255,value&255))
        return Image.frombytes('RGB',(160,144),pixels)

class SameBoy:
    reference_metadata={'emulator':'SameBoy','version':'1.0.3','bootRom':'SameBoy 1.0.3 open-source DMG boot ROM','model':'DMG-B','sourceRevision':REVISION,'bootRomSha256':BUILD['bootRomSha256'],'referenceDllSha256':BUILD['dllSha256']}
    def __init__(self,rom,**ignored):
        self.handle=DLL.ref_open(str(Path(rom).resolve()).encode(),str(BOOT).encode())
        if not self.handle:raise RuntimeError('Cannot initialize original reference')
        if DLL.ref_model(self.handle)!=2:
            DLL.ref_close(self.handle);self.handle=None
            raise RuntimeError('Reference model must be DMG-B')
        self.memory=Memory(self);self.register_file=Registers(self);self.screen=Screen(self)
        self.hooks={};self.last_error=None;self.hook_cycles=None
        def hook(_,address,bank,cycles):
            target=self.hooks.get((bank,address))
            if target:
                self.hook_cycles=cycles
                try:target[0](target[1])
                except BaseException as error:self.last_error=error;DLL.ref_fail(self.handle)
                finally:self.hook_cycles=None
        self.callback=HOOK(hook);DLL.ref_hook(self.handle,self.callback)
    def hook_register(self,bank,address,callback,context):
        if (bank,address) in self.hooks:raise ValueError('Duplicate reference hook')
        self.hooks[(bank,address)]=(callback,context);DLL.ref_watch(self.handle,address)
    def set_emulation_speed(self,speed):
        if speed!=0:raise ValueError('Reference is measured without host throttling')
    def tick(self,count=1,render=True):
        if DLL.ref_tick(self.handle,count):raise self.last_error or RuntimeError('Reference stopped')
    def button_press(self,key):DLL.ref_key(self.handle,KEYS[key],1)
    def button_release(self,key):DLL.ref_key(self.handle,KEYS[key],0)
    def _cycles(self):return self.hook_cycles if self.hook_cycles is not None else DLL.ref_cycles(self.handle)
    def save_state(self,stream):
        if DLL.ref_save(self.handle,str(Path(stream.name).resolve()).encode()):raise RuntimeError('Cannot save reference state')
    def load_state(self,stream):
        if DLL.ref_load(self.handle,str(Path(stream.name).resolve()).encode()):raise RuntimeError('Cannot load reference state')
    def stop(self,save=False):
        if self.handle:DLL.ref_close(self.handle);self.handle=None
