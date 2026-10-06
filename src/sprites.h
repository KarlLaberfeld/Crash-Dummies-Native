#pragma once
#include <array>
#include <cstdint>
#include <vector>
#include <stdexcept>
#include <algorithm>

namespace ticd {
constexpr int Width=160, Height=144, PlayHeight=136;
using SpriteColors=std::array<uint8_t,128>;
struct SpritePiece { int x=0,y=0,flags=0,chunk=-1; SpriteColors colors{}; };
struct Frame {
    std::array<uint8_t,8> meta{};
    std::array<uint8_t,96*96> pixels{}; // Composite retained for offline previews.
    std::vector<SpritePiece> pieces;
    std::vector<SpriteColors> resource; // Decoded 32-byte transfer chunks.
};
template<class Reader> void readSpritePieces(Reader& r,Frame& frame){
    int count=r.byte();if(count>40)throw std::runtime_error("Invalid sprite piece count.");
    for(int i=0;i<count;++i){SpritePiece p;p.x=static_cast<int8_t>(r.byte());p.y=static_cast<int8_t>(r.byte());p.flags=r.byte();
        r.raw(p.colors.data(),p.colors.size());for(auto color:p.colors)if(color>3)throw std::runtime_error("Invalid sprite color index.");
        frame.pieces.push_back(p);
    }
}

template<class Reader> void readSpriteResources(Reader& r,std::vector<Frame>& frames,int count,int capacity){
    for(int i=0;i<count;++i){auto& frame=frames[i];int chunks=r.byte();
        if(chunks>capacity)throw std::runtime_error("Sprite resource exceeds its buffer.");
        frame.resource.resize(chunks);
        for(auto& colors:frame.resource){r.raw(colors.data(),colors.size());
            for(auto color:colors)if(color>3)throw std::runtime_error("Invalid resource color index.");}
        for(auto& piece:frame.pieces){piece.chunk=r.byte();
            if(piece.chunk>=capacity||(chunks&&piece.chunk>=chunks))throw std::runtime_error("Invalid resource piece index.");}
    }
}

// The original uploads into the other decoded sprite resource, then swaps
// on completion (3f69 / 193e). This is asset buffering, not hardware execution.
class SpriteResources {
    std::array<std::array<SpriteColors,13>,2> buffers{};
    int active=0;
public:
    void reset(const Frame& initial){buffers={};active=0;
        if(initial.resource.size()>13)throw std::runtime_error("Sprite resource exceeds its buffer.");
        std::copy(initial.resource.begin(),initial.resource.end(),buffers[0].begin());}
    void advance(const Frame& frame,int remaining){
        int offset=static_cast<int>(frame.resource.size())-remaining;
        if(frame.resource.size()>13||offset<0||remaining<=0)throw std::runtime_error("Invalid sprite resource progress.");
        int count=std::min(4,remaining);
        std::copy_n(frame.resource.begin()+offset,count,buffers[active^1].begin()+offset);
        if(remaining<=4)active^=1;
    }
    const SpriteColors& colors(int chunk)const{return buffers[active].at(chunk);}
};

// Native composition of the game's decoded 8x16 sprite pieces. No video memory,
// CPU, DMA, or scanline execution is emulated here.
class SpriteLayer {
public:
    struct Entry { bool present=false;int x=0,y=0,flags=0;SpriteColors colors{}; };
    std::array<Entry,40> slots{};
    explicit SpriteLayer(bool reverse):cursor(reverse?39:0),direction(reverse?-1:1){}
    bool exhausted() const {return full;}
    int unusedFirst()const{return direction>0?std::clamp(cursor,0,40):0;}
    int unusedCount()const{return direction>0?40-unusedFirst():std::clamp(cursor+1,0,40);}
    bool descending()const{return direction<0;}
    int preparedSlot()const{return cursor;}
    void advancePreparedPiece(){cursor+=direction;}
    void finishPreparedEntity(){full=cursor<0||cursor>=40;}
    void clearUnused(){for(int i=unusedFirst();i<unusedFirst()+unusedCount();++i)slots[i].present=false;}
    void add(const Frame& frame,int x,int y,int flags,const SpriteResources* resources=nullptr){
        if(full)return;
        x+=static_cast<int8_t>(frame.meta[0]);y+=static_cast<int8_t>(frame.meta[1]);
        if(x < -2*frame.meta[6]-16||x>176||y < -2*frame.meta[7]-16||y>152)return;
        x+=frame.meta[6]+8;y+=frame.meta[7]+16;
        // 00:1cfd-1d3d filters byte coordinates before advancing the slot.
        // Capacity is checked after a whole entity, as at 00:1c70.
        for(const auto& piece:frame.pieces){
            int sx=(x+((flags&32)?-piece.x-8:piece.x))&255;
            int sy=(y+((flags&64)?-piece.y-16:piece.y))&255;
            if(sx>=168||sy>=152)continue;
            if(cursor>=0&&cursor<40)slots[cursor]={true,sx,sy,(flags&0xe0)^piece.flags,
                resources&&piece.chunk>=0?resources->colors(piece.chunk):piece.colors};
            cursor+=direction;
        }
        full=cursor<0||cursor>=40;
    }
    void draw(std::array<uint8_t,Width*Height>& screen,int finalPlayRowLimit=Width,
              std::array<uint8_t,Width*Height>* paletteOwners=nullptr) const{
        if(finalPlayRowLimit<0||finalPlayRowLimit>Width)throw std::runtime_error("Invalid final-row object limit");
        for(int y=0;y<PlayHeight;++y){
            std::array<int,10> selected{};int count=0;
            for(int i=0;i<40&&count<10;++i){const auto& e=slots[i];
                if(e.present&&y>=e.y-16&&y<e.y)selected[count++]=i;
            }
            // DMG overlap priority: smaller X, then smaller slot index. The
            // first ten Y matches are selected before this ordering is applied.
            std::stable_sort(selected.begin(),selected.begin()+count,[&](int a,int b){return slots[a].x<slots[b].x;});
            for(int x=0;x<(y==PlayHeight-1?finalPlayRowLimit:Width);++x)for(int n=0;n<count;++n){const auto& e=slots[selected[n]];
                int sx=x-(e.x-8),sy=y-(e.y-16);if(sx<0||sx>=8)continue;
                if(e.flags&32)sx=7-sx;if(e.flags&64)sy=15-sy;
                int color=e.colors[sy*8+sx];if(!color)continue;
                auto& background=screen[y*Width+x];
                if(!(e.flags&128)||!background){int palette=(e.flags&16)?0xe0:0xc4;background=(palette>>(color*2))&3;
                    if(paletteOwners)(*paletteOwners)[y*Width+x]=(e.flags&16)?2:1;}
                // A background-masked winning piece also masks lower objects.
                break;
            }
        }
    }
private:
    int cursor,direction;
    bool full=false;
};
int runSpriteTests();
}
