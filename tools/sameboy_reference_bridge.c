/* Separate original-ROM reference adapter. Never part of CrashDummies.exe. */
#include "Core/gb.h"
#include <stdlib.h>
#include <string.h>
typedef void (*Hook)(void *,unsigned,unsigned,uint64_t);
typedef struct {
    GB_gameboy_t *gb;uint64_t cycles8,frames;
    uint32_t pixels[160*144];Hook hook;
    uint8_t watches[65536];int failed,peeking;
} Reference;
__declspec(dllexport) const char *ref_version(void){return GB_VERSION;}
__declspec(dllexport) unsigned ref_model(Reference *r){return GB_get_model(r->gb);}
static uint32_t rgb(GB_gameboy_t *gb,uint8_t r,uint8_t g,uint8_t b){(void)gb;return (r<<16)|(g<<8)|b;}
static void frame(GB_gameboy_t *gb,GB_vblank_type_t type){(void)type;Reference *r=GB_get_user_data(gb);++r->frames;}
static uint8_t read_callback(GB_gameboy_t *gb,uint16_t address,uint8_t data){
    Reference *r=GB_get_user_data(gb);
    /* SameBoy increments PC before its opcode bus read. Watched addresses
       are identified instruction boundaries, never patched opcodes. */
    if(!r->peeking&&r->hook&&r->watches[address]&&GB_get_registers(gb)->pc==(uint16_t)(address+1)){
        size_t size;uint16_t bank=0;
        if(address>=0x4000&&address<0x8000)GB_get_direct_access(gb,GB_DIRECT_ACCESS_ROM,&size,&bank);
        r->hook(r,address,bank,(r->cycles8+gb->cycles_since_run)/2);
    }
    return data;
}
__declspec(dllexport) Reference *ref_open(const char *rom,const char *boot){
    Reference *r=calloc(1,sizeof(*r));if(!r)return NULL;
    r->gb=GB_init(GB_alloc(),GB_MODEL_DMG_B);if(!r->gb){free(r);return NULL;}
    GB_set_user_data(r->gb,r);GB_set_palette(r->gb,&GB_PALETTE_GREY);
    GB_set_pixels_output(r->gb,r->pixels);GB_set_rgb_encode_callback(r->gb,rgb);GB_set_vblank_callback(r->gb,frame);
    if(GB_load_rom(r->gb,rom)||GB_load_boot_rom(r->gb,boot)){GB_free(r->gb);GB_dealloc(r->gb);free(r);return NULL;}
    GB_set_read_memory_callback(r->gb,read_callback);return r;
}
__declspec(dllexport) void ref_close(Reference *r){if(r){GB_free(r->gb);GB_dealloc(r->gb);free(r);}}
__declspec(dllexport) void ref_hook(Reference *r,Hook hook){r->hook=hook;}
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
