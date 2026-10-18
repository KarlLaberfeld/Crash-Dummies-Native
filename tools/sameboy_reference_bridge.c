/* Separate original-ROM reference adapter. Never part of CrashDummiesNative.exe. */
#include "Core/gb.h"
#include <stdlib.h>
#include <string.h>
typedef void (*Hook)(void *,unsigned,unsigned,uint64_t);
typedef void (*BusHook)(void *,unsigned,unsigned,unsigned,unsigned,uint64_t);
typedef struct {
    GB_gameboy_t *gb;uint64_t cycles8,frames;
    uint32_t pixels[160*144];Hook hook;BusHook bus;
    uint8_t watches[65536];int failed,peeking;
} Reference;
__declspec(dllexport) const char *ref_version(void){return GB_VERSION;}
__declspec(dllexport) const char *ref_observer(void){return "execution-callback-v1";}
__declspec(dllexport) const char *ref_graphics_observer(void){return "direct-vram-pause-v1";}
__declspec(dllexport) unsigned ref_model(Reference *r){return GB_get_model(r->gb);}
static uint32_t rgb(GB_gameboy_t *gb,uint8_t r,uint8_t g,uint8_t b){(void)gb;return (r<<16)|(g<<8)|b;}
static void frame(GB_gameboy_t *gb,GB_vblank_type_t type){(void)type;Reference *r=GB_get_user_data(gb);++r->frames;}
static uint8_t read_callback(GB_gameboy_t *gb,uint16_t address,uint8_t data){
    Reference *r=GB_get_user_data(gb);
    if(!r->peeking&&r->bus&&(address==0xFF41||(address>=0x8000&&address<0xA000)))
        r->bus(r,0,address,data,GB_get_registers(gb)->pc,(r->cycles8+gb->cycles_since_run)/2);
    return data;
}
static void execution_callback(GB_gameboy_t *gb,uint16_t address,uint8_t opcode){
    (void)opcode;Reference *r=GB_get_user_data(gb);
    /* The public execution observer excludes the dummy PC read during IRQ
       entry. A read callback alone can incorrectly report that as a stage. */
    if(r->hook&&r->watches[address]){
        size_t size;uint16_t bank=0;
        if(address>=0x4000&&address<0x8000)GB_get_direct_access(gb,GB_DIRECT_ACCESS_ROM,&size,&bank);
        r->hook(r,address,bank,(r->cycles8+gb->cycles_since_run)/2);
    }
}
static bool write_callback(GB_gameboy_t *gb,uint16_t address,uint8_t data){
    Reference *r=GB_get_user_data(gb);
    if(r->bus&&((address>=0x8000&&address<0xA000)||address==0xFF40))
        r->bus(r,1,address,data,GB_get_registers(gb)->pc,(r->cycles8+gb->cycles_since_run)/2);
    /* Observe attempted writes without suppressing or replacing them. */
    return true;
}
__declspec(dllexport) Reference *ref_open(const char *rom,const char *boot){
    Reference *r=calloc(1,sizeof(*r));if(!r)return NULL;
    r->gb=GB_init(GB_alloc(),GB_MODEL_DMG_B);if(!r->gb){free(r);return NULL;}
    GB_set_user_data(r->gb,r);GB_set_palette(r->gb,&GB_PALETTE_GREY);
    GB_set_pixels_output(r->gb,r->pixels);GB_set_rgb_encode_callback(r->gb,rgb);GB_set_vblank_callback(r->gb,frame);
    if(GB_load_rom(r->gb,rom)||GB_load_boot_rom(r->gb,boot)){GB_free(r->gb);GB_dealloc(r->gb);free(r);return NULL;}
    GB_set_read_memory_callback(r->gb,read_callback);GB_set_write_memory_callback(r->gb,write_callback);
    GB_set_execution_callback(r->gb,execution_callback);return r;
}
__declspec(dllexport) void ref_close(Reference *r){if(r){GB_free(r->gb);GB_dealloc(r->gb);free(r);}}
__declspec(dllexport) void ref_hook(Reference *r,Hook hook){r->hook=hook;}
__declspec(dllexport) void ref_bus_hook(Reference *r,BusHook hook){r->bus=hook;}
/* Reference diagnostics only. These fields never enter a native clock. */
__declspec(dllexport) void ref_lcd_snapshot(Reference *r,unsigned *out){
    GB_gameboy_t *g=r->gb;
    out[0]=g->io_registers[GB_IO_LCDC];out[1]=g->io_registers[GB_IO_STAT];
    out[2]=g->io_registers[GB_IO_SCX];out[3]=g->io_registers[GB_IO_SCY];
    out[4]=g->io_registers[GB_IO_WX];out[5]=g->io_registers[GB_IO_WY];out[6]=g->io_registers[GB_IO_LY];
    out[7]=g->current_line;out[8]=g->cycles_for_line;out[9]=g->display_cycles;
    out[10]=g->vram_read_blocked;out[11]=g->vram_write_blocked;
}
/* Read-only accepted storage, without a CPU bus access or PPU synchronization.
   The public direct-access API is confined to the two identified pause areas. */
__declspec(dllexport) int ref_pause_graphics(Reference *r,uint8_t *out){
    size_t size;uint16_t bank;const uint8_t *vram=GB_get_direct_access(r->gb,GB_DIRECT_ACCESS_VRAM,&size,&bank);
    if(!vram||size<0x1C14||bank!=0)return 0;
    memcpy(out,vram+0x1C00,20);memcpy(out+20,vram+0x0F80,128);return 1;
}
__declspec(dllexport) void ref_watch(Reference *r,unsigned address){if(address<65536)r->watches[address]=1;}
__declspec(dllexport) void ref_fail(Reference *r){r->failed=1;}
__declspec(dllexport) int ref_tick(Reference *r,unsigned frames){
    uint64_t target=r->frames+frames;
    while(r->frames<target&&!r->failed)r->cycles8+=GB_run(r->gb);
    return r->failed;
}
__declspec(dllexport) uint8_t ref_peek(Reference *r,unsigned address){
    r->peeking=1;uint8_t value=GB_read_memory(r->gb,address);r->peeking=0;return value;
}
__declspec(dllexport) unsigned ref_reg(Reference *r,unsigned index){return index<6?GB_get_registers(r->gb)->registers[index]:0;}
__declspec(dllexport) void ref_key(Reference *r,unsigned key,int pressed){GB_set_key_state(r->gb,key,pressed);}
__declspec(dllexport) uint64_t ref_cycles(Reference *r){return r->cycles8/2;}
__declspec(dllexport) void *ref_pixels(Reference *r){return r->pixels;}
__declspec(dllexport) int ref_save(Reference *r,const char *path){return GB_save_state(r->gb,path);}
__declspec(dllexport) int ref_load(Reference *r,const char *path){r->failed=0;r->cycles8=r->frames=0;return GB_load_state(r->gb,path);}
