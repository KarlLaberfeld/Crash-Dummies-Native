#include "ui.h"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <stdexcept>
namespace ticd {
UiAssets UiAssets::load(const std::wstring& path){
    FILE* f=_wfopen(path.c_str(),L"rb");if(!f)throw std::runtime_error("ui.dat is missing. Rebuild with the original ROM.");
    std::vector<uint8_t> data(1024*1024);size_t n=fread(data.data(),1,data.size(),f);int extra=fgetc(f);fclose(f);data.resize(n);
    if(n<8||extra!=EOF||memcmp(data.data(),"TICDUI02",8))throw std::runtime_error("Invalid UI asset package.");
    UiAssets a;size_t offset=8;
    auto read=[&](auto& target){if(target.size()>data.size()-offset)throw std::runtime_error("Truncated UI package");
        memcpy(target.data(),data.data()+offset,target.size());offset+=target.size();};
    read(a.tiles);read(a.titleBackground);for(auto& m:a.titleMaps)read(m);read(a.initialScores);
    for(auto& instruction:a.instructions){read(instruction.tiles);read(instruction.map);
        std::array<uint8_t,2> length{};read(length);size_t count=length[0]+256*length[1];
        if(!count||count>4096)throw std::runtime_error("Invalid instruction text length");
        instruction.text.resize(count);read(instruction.text);}
    for(auto& m:a.headers)read(m);for(auto& t:a.resultTiles)read(t);
    for(auto& m:a.resultTexts)read(m);for(auto& m:a.resultLayouts)read(m);
    read(a.endingTiles);for(auto& m:a.endings)read(m);
    read(a.names);read(a.skiQuotas);read(a.bombQuotas);read(a.startPrompt);
    if(offset!=data.size())throw std::runtime_error("Trailing UI package data");
    auto validate=[](const auto& tiles){for(int shade:tiles)if(shade>3)throw std::runtime_error("Invalid UI palette");};
    validate(a.tiles);validate(a.titleBackground);for(const auto& i:a.instructions)validate(i.tiles);
    for(const auto& t:a.resultTiles)validate(t);validate(a.endingTiles);return a;
}

std::array<uint8_t,Width*Height> renderTitle(const UiAssets& a,int page,bool twoPlayers,int ticks){
    if(page<0||page>=6)throw std::invalid_argument("Invalid title page");
    auto screen=a.titleBackground;
    // 00:2502-2535: stable phase uses unsigned window-map tiles with SCY=88
    // between the two fixed signed-tile logo strips at scanlines 24 and 104.
    for(int y=24;y<104;++y)for(int x=0;x<Width;++x){int wy=y+88,tile=a.titleMaps[page][(wy/8)*32+x/8];
        screen[y*Width+x]=a.tiles[tile*64+(wy&7)*8+(x&7)];}
    if(page==5){int tile=254+((ticks>>4)&1),py=56+(twoPlayers?16:0);
        for(int y=0;y<8;++y)for(int x=0;x<8;++x){int shade=a.tiles[tile*64+y*8+x];if(shade)screen[(py+y)*Width+16+x]=(0xc4>>(shade*2))&3;}}
    return screen;
}
namespace {
std::array<uint8_t,Width*Height> renderMap(const UiTiles& tiles,const UiMap& map,int scroll=0){
    std::array<uint8_t,Width*Height> screen{};
    for(int y=0;y<Height;++y)for(int x=0;x<Width;++x){
        int wy=(y+(y>=96?scroll:0))&255;
        int tile=map[(wy/8)*32+x/8];screen[y*Width+x]=tiles[tile*64+(wy&7)*8+(x&7)];
    }return screen;
}
void overlay(UiMap& dest,const UiMap& source){for(size_t i=0;i<dest.size();++i)if(source[i])dest[i]=source[i];}
void money(UiMap& map,int row,int value){
    int digits[6];for(int i=5;i>=0;--i){digits[i]=value%10;value/=10;}
    int first=0;while(first<3&&!digits[first])++first;
    for(int i=0;i<4;++i)map[row*32+13+i]=i<first?0:digits[i]+1;
    map[row*32+12+first]=0x33;map[row*32+17]=0x2c;
    map[row*32+18]=digits[4]+1;map[row*32+19]=digits[5]+1;
}
int resultText(int stunt,int flags){
    if(flags&2)return stunt;
    switch(stunt){
    case 0:return flags&16?6:flags&32?7:flags&128?8:5;
    case 1:return flags&16?10:9;
    case 2:return flags&32?12:11;
    case 3:return 13;
    default:return flags&16?15:14;
    }
}
}
void UiFlow::beginInstructions(){
    const auto& player=campaign.players[campaign.current];stunt=player.day;level=player.difficulty;
    phase=UiPhase::Instructions;phaseTicks=0;scroll=0;position=anchor=row=speed=delay=0;scrollStep=pendingGlyph=-1;
    cursor=0;textDone=false;map=assets.instructions[stunt].map;
    overlay(map,assets.headers[(campaign.current*5+stunt)*4+level]);map[19]=static_cast<uint8_t>(std::min(player.lives,9)+1);
    text.clear();
    // Resolve the identified text macros into glyphs. Their 0x88 terminators
    // never become native operations or cartridge return addresses.
    for(int op:assets.instructions[stunt].text){
        if(op==0x89){auto start=assets.names.begin()+campaign.current*5;text.insert(text.end(),start,start+5);}
        else if(op==0x8a||op==0x8c){const auto& quota=op==0x8a?assets.skiQuotas:assets.bombQuotas;text.push_back(quota[level*3]);text.push_back(quota[level*3+1]);}
        else text.push_back(static_cast<uint8_t>(op));
    }
    advanceText();
}
void UiFlow::advanceText(){
    auto byte=[&](){if(cursor>=text.size())throw std::runtime_error("Truncated instruction text");return text[cursor++];};
    auto put=[&](int glyph){if(position<0||position>=1024)throw std::runtime_error("Instruction text outside map");map[position++]=static_cast<uint8_t>(glyph);};
    if(delay>0&&--delay>0)return;
    if(pendingGlyph>=0){put(pendingGlyph);pendingGlyph=-1;}
    if(scrollStep>=0){constexpr int increments[]={1,2,3,1,1};scroll=(scroll+increments[scrollStep++])&255;
        if(scrollStep<5){delay=2;return;}scrollStep=-1;position=(++row)*32+anchor;}
    while(!textDone){int op=byte();
        if(op<128){if(op&&speed){pendingGlyph=op;delay=speed;return;}put(op);}
        else switch(op){
        case 0x80:for(int glyph:assets.startPrompt)put(glyph);textDone=true;return;
        case 0x81:anchor=byte();row=byte();position=row*32+anchor;break;
        case 0x82:if(byte()!=0)throw std::runtime_error("Unexpected instruction text layer");break;
        case 0x84:position=(++row)*32+anchor;break;
        case 0x85:scrollStep=0;delay=2;return;
        case 0x86:speed=byte();break;
        case 0x87:if(byte()!=8)throw std::runtime_error("Unexpected instruction skip input");break;
        default:throw std::runtime_error("Unsupported instruction text operation");
        }
    }
}
void UiFlow::finishStunt(int flags,int earned,int seconds,int extraLives,int flagsCollected){
    if(phase!=UiPhase::Playing)throw std::logic_error("Stunt result outside gameplay");
    campaign.settle(flags,earned,seconds,extraLives);flagsHit=flagsCollected;
    phase=UiPhase::Result;phaseTicks=0;
}
void UiFlow::continueCampaign(){
    if(campaign.next())beginInstructions();else{phase=UiPhase::Title;page=0;phaseTicks=0;}
}
void UiFlow::step(int buttons){
    int pressed=buttons&~previous;previous=buttons;++ticks;++phaseTicks;
    switch(phase){
    case UiPhase::Title:
        if(pressed&UiStart){campaign.start(twoPlayers);beginInstructions();}
        else if(page==5){
            if(pressed&(UiSelect|Up|Down))twoPlayers=!twoPlayers;
            if(pressed&(A|B)){page=0;phaseTicks=0;}
        }else if(pressed&UiSelect){page=5;phaseTicks=0;}
        else{constexpr int durations[]={480,480,960,480,960};
            if((pressed&(A|B))||phaseTicks>=durations[page]){page=(page+1)%5;phaseTicks=0;}}
        break;
    case UiPhase::Instructions:
        if(pressed&UiStart){phase=UiPhase::Playing;phaseTicks=0;}else if(!textDone)advanceText();break;
    case UiPhase::Result:
        // Stationary settlement presentation; the original money-count and
        // fade/raster timings are still pending reconstruction.
        if((pressed&(UiStart|A|B))||phaseTicks>=(campaign.last.success?600:480)){
            if(campaign.last.completed){phase=UiPhase::Ending;phaseTicks=0;}else continueCampaign();}
        break;
    case UiPhase::Ending:if(phaseTicks>=480)continueCampaign();break;
    case UiPhase::Playing:break;
    }
}
std::array<uint8_t,Width*Height> UiFlow::render() const{
    if(phase==UiPhase::Title)return renderTitle(assets,page,twoPlayers,ticks);
    if(phase==UiPhase::Instructions)return renderMap(assets.instructions[stunt].tiles,map,scroll);
    if(phase==UiPhase::Ending){auto canvas=assets.endings[campaign.current];overlay(canvas,assets.resultLayouts[7]);
        money(canvas,17,campaign.players[campaign.current].savings);return renderMap(assets.endingTiles,canvas);}
    if(phase==UiPhase::Result){
        const auto& result=campaign.last;int portrait=result.success?(result.perfect?2:1):0;
        auto canvas=assets.resultTexts[resultText(stunt,result.flags)];overlay(canvas,assets.resultLayouts[portrait]);
        if(result.success){
            overlay(canvas,assets.resultLayouts[3]);overlay(canvas,assets.resultLayouts[4]);
            money(canvas,15,campaign.players[campaign.current].savings);money(canvas,16,0);
            if(result.perfect){canvas[16*32+10]=0x25;canvas[16*32+11]=3;}
            if(!(result.flags&64)){overlay(canvas,assets.resultLayouts[5]);canvas[17*32+18]=1;canvas[17*32+19]=1;
                if(result.perfect){canvas[17*32+10]=0x25;canvas[17*32+11]=3;}}
            if(stunt==2){overlay(canvas,assets.resultLayouts[6]);canvas[14*32+18]=(flagsHit/10)%10+1;canvas[14*32+19]=flagsHit%10+1;}
        }else if(result.gameOver){overlay(canvas,assets.resultLayouts[7]);money(canvas,17,campaign.players[campaign.current].savings);}
        return renderMap(assets.resultTiles[portrait],canvas);
    }
    return {};
}
}
