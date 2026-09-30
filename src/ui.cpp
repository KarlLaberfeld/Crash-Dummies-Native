#include "ui.h"
#include <cstdio>
#include <cstring>
#include <stdexcept>
namespace ticd {
UiAssets UiAssets::load(const std::wstring& path){
    FILE* f=_wfopen(path.c_str(),L"rb");if(!f)throw std::runtime_error("ui.dat is missing. Rebuild with the original ROM.");
    constexpr size_t size=8+256*64+Width*Height+6*1024+48;
    std::vector<uint8_t> data(size);size_t n=fread(data.data(),1,size,f);int extra=fgetc(f);fclose(f);
    if(n!=size||extra!=EOF||memcmp(data.data(),"TICDUI01",8))throw std::runtime_error("Invalid UI asset package.");
    UiAssets a;size_t offset=8;auto read=[&](auto& target){memcpy(target.data(),data.data()+offset,target.size());offset+=target.size();};
    read(a.tiles);read(a.titleBackground);for(auto& m:a.titleMaps)read(m);read(a.initialScores);
    for(int shade:a.tiles)if(shade>3)throw std::runtime_error("Invalid UI tile palette.");
    for(int shade:a.titleBackground)if(shade>3)throw std::runtime_error("Invalid title palette.");return a;
}
std::array<uint8_t,Width*Height> renderTitle(const UiAssets& a,int page,bool twoPlayers,int ticks){
    if(page<0||page>=6)throw std::invalid_argument("Invalid title page");
    auto screen=a.titleBackground;
    // 00:2502-2535: stable phase uses unsigned window-map tiles with SCY=88
    // between the two fixed signed-tile logo strips at scanlines 24 and 104.
    for(int y=24;y<104;++y)for(int x=0;x<Width;++x){int wy=y+88,tile=a.titleMaps[page][(wy/8)*32+x/8];
        screen[y*Width+x]=a.tiles[tile*64+(wy&7)*8+(x&7)];}
    if(page==5){int tile=254+((ticks>>4)&1),py=56+(twoPlayers?16:0);
        for(int y=0;y<8;++y)for(int x=0;x<8;++x){int shade=a.tiles[tile*64+y*8+x];if(shade)screen[(py+y)*Width+16+x]=shade;}}
    return screen;
}
}
