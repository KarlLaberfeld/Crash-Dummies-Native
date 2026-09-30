#pragma once
#include <array>
#include <cstdint>
#include <vector>
#include <stdexcept>
#include <algorithm>

namespace ticd {
constexpr int Width=160, Height=144, PlayHeight=136;
struct SpritePiece { int x=0,y=0,flags=0; std::array<uint8_t,128> colors{}; };
struct Frame {
    std::array<uint8_t,8> meta{};
    std::array<uint8_t,96*96> pixels{}; // Composite retained for offline previews.
    std::vector<SpritePiece> pieces;
};
template<class Reader> void readSpritePieces(Reader& r,Frame& frame){
    int count=r.byte();if(count>40)throw std::runtime_error("Invalid sprite piece count.");
    for(int i=0;i<count;++i){SpritePiece p;p.x=static_cast<int8_t>(r.byte());p.y=static_cast<int8_t>(r.byte());p.flags=r.byte();
        r.raw(p.colors.data(),p.colors.size());for(auto color:p.colors)if(color>3)throw std::runtime_error("Invalid sprite color index.");
        frame.pieces.push_back(p);
    }
}

// Native composition of the game's decoded 8x16 sprite pieces. No video memory,
// CPU, DMA, or scanline execution is emulated here.
class SpriteLayer {
public:
    struct Entry { const SpritePiece* piece=nullptr;int x=0,y=0,flags=0; };
    std::array<Entry,40> slots{};
    explicit SpriteLayer(bool reverse):cursor(reverse?39:0),direction(reverse?-1:1){}
    bool exhausted() const {return full;}
    void add(const Frame& frame,int x,int y,int flags){
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
            if(cursor>=0&&cursor<40)slots[cursor]={&piece,sx,sy,(flags&0xe0)^piece.flags};
            cursor+=direction;
        }
        full=cursor<0||cursor>=40;
    }
    void draw(std::array<uint8_t,Width*Height>& screen) const{
        for(int y=0;y<PlayHeight;++y){
            std::array<int,10> selected{};int count=0;
            for(int i=0;i<40&&count<10;++i){const auto& e=slots[i];
                if(e.piece&&y>=e.y-16&&y<e.y)selected[count++]=i;
            }
            // DMG overlap priority: smaller X, then smaller slot index. The
            // first ten Y matches are selected before this ordering is applied.
            std::stable_sort(selected.begin(),selected.begin()+count,[&](int a,int b){return slots[a].x<slots[b].x;});
            for(int x=0;x<Width;++x)for(int n=0;n<count;++n){const auto& e=slots[selected[n]];
                int sx=x-(e.x-8),sy=y-(e.y-16);if(sx<0||sx>=8)continue;
                if(e.flags&32)sx=7-sx;if(e.flags&64)sy=15-sy;
                int color=e.piece->colors[sy*8+sx];if(!color)continue;
                auto& background=screen[y*Width+x];
                if(!(e.flags&128)||!background){int palette=(e.flags&16)?0xe0:0xc4;background=(palette>>(color*2))&3;}
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
