#pragma once
#include "air.h"

namespace ticd {
// Source-owned 32-byte staging row and 32x32 background publication. Partial
// preparation retains old bytes; a display publishes exactly the staged row.
struct AirMapPublication {
    std::array<uint8_t,32> buffer{};
    std::array<uint8_t,1024> tiles{};
    int destination=0;
    static int destinationRow(int oldCamera){return ((oldCamera>>7)+24)&31;}
    static uint8_t cellTile(const AirGame& game,int oldCamera,int camera,int cell,int half){
        if(cell<0||cell>=16||half<0||half>1)throw std::runtime_error("Invalid staged Air row cell");
        bool down=static_cast<uint16_t>(oldCamera-camera)&0x8000;
        int row=((oldCamera>>8)-4+(down?16:0))&255;
        int meta=game.assets.levels[game.difficulty].cells[row*16+cell];
        return game.assets.quadrants[(((oldCamera>>7)&1)*2+half)*128+meta];
    }
    void publish(){std::copy(buffer.begin(),buffer.end(),tiles.begin()+32*destination);}
    void prepare(const AirGame& game,int oldCamera,int camera){
        destination=destinationRow(oldCamera);
        for(int cell=0;cell<16;++cell)for(int half=0;half<2;++half)buffer[2*cell+half]=cellTile(game,oldCamera,camera,cell,half);
    }
    void initialize(const AirGame& game,const std::array<uint8_t,1024>* inherited=nullptr){
        buffer.fill(0);if(inherited)tiles=*inherited;else tiles.fill(0);destination=0;int oldCamera=0;
        // 1e77 prepares/copies 32 rows while LCD-off. The source first row
        // starts with the cleared previous camera; later rows step upward.
        for(int row=0;row<32;++row){int camera=(game.cameraY+0x1000-128*row)&65535;
            if(((oldCamera^camera)&128)!=0){prepare(game,oldCamera,camera);publish();}oldCamera=camera;}
    }
    int pixel(const AirGame& game,int x,int y)const{
        if(x<0||x>=Width||y<0||y>=PlayHeight)throw std::runtime_error("Invalid Air background pixel");
        int wx=(game.visibleCameraX>>4)+x,wy=(game.visibleCameraY>>4)+y;
        int tile=tiles[((wy>>3)&31)*32+((wx>>3)&31)];
        if(tile>=128)throw std::runtime_error("Unowned Air background tile");
        return game.assets.tiles[tile*64+(wy&7)*8+(wx&7)];
    }
    void render(AirGame& game,std::array<uint8_t,Width*Height>* owners=nullptr)const{
        if(owners)owners->fill(0);
        for(int y=0;y<PlayHeight;++y)for(int x=0;x<Width;++x)game.screen[y*Width+x]=pixel(game,x,y);
        game.visibleSprites.draw(game.screen,Width,owners);
        for(int col=0;col<20;++col)for(int y=0;y<8;++y)for(int x=0;x<8;++x)
            game.screen[(PlayHeight+y)*Width+col*8+x]=game.assets.hudTiles[game.hudMap[col]*64+y*8+x];
    }
};
}
