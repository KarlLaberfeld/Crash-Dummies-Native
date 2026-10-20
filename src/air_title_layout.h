#pragma once
#include "air_title_reset.h"

namespace ticd {
struct AirTitleCommand {int kind=0,a=0,b=0,width=0,height=0;std::vector<uint8_t> cells;};
struct AirTitleLayoutAssets {
    std::vector<AirTitleCommand> commands;
    void validate()const{
        static constexpr int order[]={0,1,2,1,2,0,1,2,1,2,3};
        if(commands.size()!=11)throw std::runtime_error("Incomplete static title layout");
        int x=0,y=0;
        for(int i=0;i<11;++i){const auto& c=commands[i];
            if(c.kind!=order[i]||c.a<0||c.b<0||c.width<0||c.height<0)throw std::runtime_error("Unowned title command order");
            if(c.kind==0){if(c.a!=(i==5)||c.b)throw std::runtime_error("Unowned title layer order");}
            if(c.kind==1){if(c.a>31||c.b>31)throw std::runtime_error("Invalid title anchor");x=c.a;y=c.b;}
            if(c.kind==2){if(c.a||c.b||c.width<1||c.height<1||x+c.width>32||y+c.height>32||c.cells.size()!=size_t(c.width*c.height))throw std::runtime_error("Invalid title rectangle cells");}
            else if(c.width||c.height||!c.cells.empty())throw std::runtime_error("Unexpected title rectangle payload");
            if(c.kind==3&&(c.a||c.b))throw std::runtime_error("Invalid title terminator");
        }
    }
    static AirTitleLayoutAssets load(const char* path){
        std::ifstream file(path,std::ios::binary);char magic[8];uint8_t count[2];AirTitleLayoutAssets data;
        if(!file.read(magic,8)||std::string(magic,8)!="CDNTL001"||!file.read(reinterpret_cast<char*>(count),2)||count[0]!=11||count[1])throw std::runtime_error("Missing static title layout");
        for(int i=0;i<11;++i){uint8_t header[5];if(!file.read(reinterpret_cast<char*>(header),5))throw std::runtime_error("Truncated title command");
            AirTitleCommand c{header[0],header[1],header[2],header[3],header[4],{}};
            if(c.kind==2){if(c.width<1||c.width>32||c.height<1||c.height>32)throw std::runtime_error("Invalid title rectangle dimensions");
                c.cells.resize(c.width*c.height);if(!file.read(reinterpret_cast<char*>(c.cells.data()),c.cells.size()))throw std::runtime_error("Truncated title cells");}
            data.commands.push_back(std::move(c));}
        if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Trailing title data");data.validate();return data;
    }
};
struct AirTitleLayout {AirTitleReset reset;int lyc=-1,windowX=-1,windowY=-1;bool bootShown=true;};
// 0206..0258: a completed campaign necessarily passed the one-time boot
// screen. Only that post-campaign branch is owned here. Layout rectangles are
// decoded local assets, not source code. Ends before EI; pending services,
// initial display geometry and subsequent fade still require separate owners.
template<class Boundary,class Write>
AirTitleLayout airTitleLayout(AirTitleReset reset,bool bootShown,const NativeAudio& sound,
    const AirTitleLayoutAssets& assets,Boundary&& boundary,Write&& write){
    if(!bootShown||!reset.servicesMasked||reset.lcdc!=0x5b||reset.bank!=1||reset.display||reset.stat||reset.pendingRequests!=3||
       reset.timing.displays!=546||reset.timing.stats!=546||reset.timing.countdown!=54||reset.timing.input.held!=255||
       !sound.enabled||sound.song!=13)throw std::runtime_error("Unowned post-campaign title layout entry");
    assets.validate();AirTitleLayout state;state.reset=std::move(reset);auto& r=state.reset;auto& t=r.timing;
    int64_t now=t.end;int command=-1,row=-1,layer=0x9800,x=0,y=0;
    auto point=[&](const char* name){t.end=now;boundary(name,now,command,row,state);};
    point("begin");now+=16+4+12;point("bootSkipped");
    now+=8;write(now,0xc099,1);now+=16;r.stat=1;point("callbackReady");
    // RST's identified trampoline includes the 0010 JP before layout entry.
    now+=8+4+8;point("layoutCall");now+=16+16+12+16+4+16+4;
    for(const auto& c:assets.commands){++command;point("command");
        if(c.kind==0){now+=236;layer=0x9800+1024*c.a;}
        else if(c.kind==1){now+=352;x=c.a;y=c.b;}
        else if(c.kind==3){now+=276;}
        else{
            now+=168+188;point("rectangleEntry");
            now+=12+12+16+12+60+16;r.bank=7;
            for(row=0;row<c.height;++row){
                int destination=layer+32*(y+row)+x;now+=16+16;
                for(int column=0;column<c.width;++column){
                    now+=8+24+16+12+8+8+12;int value=c.cells[row*c.width+column];write(now,destination+column,value);
                    (layer==0x9800?r.background:r.window)[32*(y+row)+x+column]=value;
                    now+=8+8+16+4+(column==c.width-1?8:12);
                }
                point("rowReady");
                now+=12+12+8+16+28+((destination&255)+32>255?8:0)+4+(row==c.height-1?8:12);
            }
            row=-1;now+=12+12+60;r.bank=1;point("copyReturned");now+=16+12+16;
        }
    }
    command=-1;point("layoutReturned");
    now+=8;point("statWrite");write(now,0xff41,0x44);now+=12+8;
    point("lcdWrite");write(now,0xff40,0x43);now+=12;r.lcdc=0x43;now+=8;
    point("compareWrite");write(now,0xff45,23);now+=12;state.lyc=23;now+=8;
    point("windowXWrite");write(now,0xff4b,166);now+=12;state.windowX=166;now+=8;
    point("windowYWrite");write(now,0xff4a,112);now+=12;state.windowY=112;point("lcdEnableCall");now+=24;point("lcdEnableEntry");
    now+=12+8;write(now,0xff40,0xc3);t.lcdEpoch=now+8;now+=12;r.lcdc=0xc3;point("lcdWriteReturned");now+=16;
    // Both retained requests precede these future periodic deadlines. Their
    // acceptance at EI/follower is deliberately left to the next owner.
    t.nextStat=t.lcdEpoch+23*456;t.nextVBlank=t.lcdEpoch+144*456;point("enableEntry");return state;
}
}
