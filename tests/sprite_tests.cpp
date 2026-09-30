#include "sprites.h"
#include <cstdio>
#include <stdexcept>

namespace ticd {
namespace {
Frame solid(int color,int flags=0){Frame f;f.pieces.resize(1);f.pieces[0].colors.fill(static_cast<uint8_t>(color));f.pieces[0].flags=flags;return f;}
using Image=std::array<uint8_t,Width*Height>;
}
int runSpriteTests(){
    FILE* log=fopen("sprite-test.txt","w");if(!log)return 2;int assertions=0;
    auto check=[&](bool ok,const char* message){++assertions;if(!ok)throw std::runtime_error(message);};
    try{
        auto light=solid(1),dark=solid(3),white=solid(2),transparent=solid(0),behind=solid(3,128);
        Image image{};
        SpriteLayer normal(false);normal.add(light,20,20,0);normal.add(dark,20,20,0);normal.draw(image);
        check(image[20*Width+20]==1,"Equal X overlap chooses the first slot");
        SpriteLayer reverse(true);reverse.add(light,20,20,0);reverse.add(dark,20,20,0);image.fill(0);reverse.draw(image);
        check(image[20*Width+20]==3,"Reverse slot allocation reverses equal-X overlap");
        SpriteLayer left(false);left.add(light,20,20,0);left.add(dark,19,20,0);image.fill(0);left.draw(image);
        check(image[20*Width+20]==3,"Smaller X wins even at a later slot");
        SpriteLayer clear(false);clear.add(transparent,20,20,0);clear.add(dark,20,20,0);image.fill(0);clear.draw(image);
        check(image[20*Width+20]==3,"Color index zero reveals a lower object");
        SpriteLayer whiteMask(false);whiteMask.add(white,20,20,0);whiteMask.add(dark,20,20,0);image.fill(2);whiteMask.draw(image);
        check(image[20*Width+20]==0,"A nonzero color mapped to white still masks lower objects");
        SpriteLayer backgroundMask(false);backgroundMask.add(behind,20,20,0);backgroundMask.add(light,20,20,0);image.fill(2);backgroundMask.draw(image);
        check(image[20*Width+20]==2,"Background-masked winning object also masks lower objects");
        image.fill(0);backgroundMask.draw(image);check(image[20*Width+20]==3,"Behind-background object remains visible over color zero");
        SpriteLayer xorPriority(false);xorPriority.add(behind,20,20,128);image.fill(2);xorPriority.draw(image);
        check(image[20*Width+20]==3,"Entity and piece priority flags combine by XOR");
        auto palette=solid(2,16);SpriteLayer alternate(false);alternate.add(palette,20,20,0);image.fill(0);alternate.draw(image);
        check(image[20*Width+20]==2,"Piece palette selects original OBP1 mapping");

        SpriteLayer ten(false);for(int n=0;n<10;++n)ten.add(light,30+n*8,20,0);ten.add(dark,20,20,0);image.fill(0);ten.draw(image);
        check(image[20*Width+20]==0,"The eleventh Y match is excluded before sorting by X");
        SpriteLayer hiddenX(false);for(int n=0;n<10;++n)hiddenX.add(light,-8,20,0);hiddenX.add(dark,20,20,0);image.fill(0);hiddenX.draw(image);
        check(image[20*Width+20]==0,"Invisible X=0 slots still consume the line limit");
        SpriteLayer emptyY(false);for(int n=0;n<10;++n)emptyY.add(light,20,-16,0);emptyY.add(dark,20,20,0);image.fill(0);emptyY.draw(image);
        check(image[20*Width+20]==3,"Off-screen Y does not consume visible line capacity");
        SpriteLayer transparentLimit(false);for(int n=0;n<10;++n)transparentLimit.add(transparent,20,20,0);transparentLimit.add(dark,20,20,0);image.fill(0);transparentLimit.draw(image);
        check(image[20*Width+20]==0,"Transparent tiles still consume selected slots");
        SpriteLayer lines(false);for(int n=0;n<10;++n)lines.add(light,30+n*8,20,0);lines.add(dark,20,21,0);image.fill(0);lines.draw(image);
        check(image[35*Width+20]==0&&image[36*Width+20]==3,"Selection is recomputed per line with exclusive bottom edge");

        auto forty=light;forty.pieces.assign(40,light.pieces[0]);
        SpriteLayer capacity(false);capacity.add(forty,20,-16,0);capacity.add(dark,20,20,0);image.fill(0);capacity.draw(image);
        check(image[20*Width+20]==0,"All forty slots count even when their rows are invisible");
        auto overflow=light;overflow.pieces.assign(3,light.pieces[0]);overflow.pieces[1].x=8;overflow.pieces[2].x=16;
        SpriteLayer entityEnd(false);for(int n=0;n<39;++n)entityEnd.add(light,20,-16,0);entityEnd.add(overflow,20,20,0);image.fill(0);entityEnd.draw(image);
        check(image[20*Width+20]==1&&image[20*Width+28]==0,"An entity crossing slot forty clips its excess pieces");
        SpriteLayer reverseEnd(true);for(int n=0;n<39;++n)reverseEnd.add(light,20,-16,0);reverseEnd.add(overflow,20,20,0);image.fill(0);reverseEnd.draw(image);
        check(image[20*Width+20]==1&&image[20*Width+28]==0,"Reverse allocation clips at the low slot boundary");
        SpriteLayer rejected(false);for(int n=0;n<40;++n)rejected.add(light,160,20,0);rejected.add(dark,20,20,0);image.fill(0);rejected.draw(image);
        check(image[20*Width+20]==3,"Original X>=168 piece rejection does not consume slots");

        auto corner=transparent;corner.pieces[0].colors[0]=1;
        SpriteLayer flip(false);flip.add(corner,40,40,32|64);image.fill(0);flip.draw(image);
        check(image[39*Width+39]==1,"Entity flip mirrors piece position and pixel orientation");
        corner.pieces[0].flags=32|64;SpriteLayer doubleFlip(false);doubleFlip.add(corner,40,40,32|64);image.fill(0);doubleFlip.draw(image);
        check(image[24*Width+32]==1,"Piece flip XOR entity flip cancels pixel orientation only");
        auto offset=light;offset.meta[0]=254;offset.meta[1]=253;offset.meta[6]=4;offset.meta[7]=8;
        SpriteLayer origin(false);origin.add(offset,20,20,0);image.fill(0);origin.draw(image);
        check(image[25*Width+22]==1&&image[24*Width+22]==0,"Signed origin and half extent position the emitted piece");
        SpriteLayer hud(false);hud.add(dark,20,135,0);image.fill(0);hud.draw(image);
        check(image[135*Width+20]==3&&image[136*Width+20]==0,"Sprites stop at the original HUD boundary");
        auto first=image;image.fill(0);hud.draw(image);check(first==image,"Repainting does not advance sprite allocation phase");
        fprintf(log,"PASS: %d native sprite composition assertions. Global allocation phase and reference images remain unverified.\n",assertions);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d sprite assertions: %s\n",assertions,e.what());fclose(log);return 1;}
}
}
