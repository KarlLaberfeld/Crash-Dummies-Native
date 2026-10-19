// Native-only masked reset and inherited LCD phase tests; no original data.
#include "air_title_reset.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool condition,const char* why){++checks;if(!condition)throw std::runtime_error(why);};
    try{
        AudioAssets assets;NativeAudio sound(assets);sound.enabled=true;sound.song=13;
        for(int phase:{0,1,143*456,144*456,145*456-136,145*456+100,153*456,70223}){
            AirResultTransition input;input.end=10*AirClock::Frame+phase;input.lcdEpoch=0;
            input.nextStat=11*AirClock::Frame+143*456;input.nextVBlank=11*AirClock::Frame+144*456;
            input.tick=65535;input.countdown=54;input.displays=input.stats=546;input.input={33,8,1};
            int writes=0,polls=0,points=0;int64_t previous=0;std::vector<int> lines;
            auto result=airTitleResetPrefix(input,sound,
                [&](const char*,int64_t cycle,const AirTitleReset& r){require(cycle>=input.end&&cycle>previous,"Reset points advance from actual parent");previous=cycle;++points;
                    require(r.timing.tick==65535&&r.timing.displays==546&&r.timing.countdown==54,"Masked work cannot advance services");},
                [&](int64_t,int line){++polls;lines.push_back(line);},
                [&](int64_t,int address,int value){
                    if(writes<1024)require(address==0x9c00+writes&&value==0,"Window clear retains all 1024 cells");
                    else if(writes<2048)require(address==0x9800+writes-1024&&value==0,"Background clear retains all 1024 cells");
                    else if(writes<2304)require(address==0xc100+writes-2048&&value==0,"Object clear includes unused list tail");
                    else require(value==(address==0xff8a?255:0),"Reset stores preserve the distinct held-button sentinel");
                    ++writes;});
            require(writes==2320&&points==10,"Complete masked reset scope");
            require(polls>0&&polls<=2200&&lines.back()==145,"Native inherited phase reaches line 145");
            for(size_t i=0;i+1<lines.size();++i)require(lines[i]!=145,"Equality wait cannot continue past matching line");
            require(result.servicesMasked&&result.bank==1&&result.lcdc==0x5b,"Return leaves services/LCD masked and native data bank selected");
            require(result.timing.input.held==255&&result.timing.input.pressed==1&&result.timing.input.previous==8,"Title sentinel does not resample or erase an existing edge");
            require(result.timing.lcdEpoch==input.lcdEpoch&&result.timing.nextStat==input.nextStat&&result.timing.nextVBlank==input.nextVBlank,"Old LCD deadlines remain history; caller must restart before services");
            require(sound.enabled&&sound.song==13,"Masked prefix does not stop or service music");
            const int pending=(input.nextStat<=result.lcdDisabled?2:0)|(input.nextVBlank<=result.lcdDisabled?1:0);
            require(result.pendingRequests==pending,"Only requests reached before LCD disable become pending");
        }
        for(int mode=0;mode<8;++mode){
            AirResultTransition input;input.end=10*AirClock::Frame;input.nextStat=input.end+1;input.nextVBlank=input.end+100;
            input.countdown=54;input.displays=input.stats=546;
            if(mode==0)input.lives=1;if(mode==1)--input.displays;if(mode==2)--input.stats;if(mode==3)--input.countdown;
            if(mode==4)input.lcdEpoch=input.end;if(mode==5)input.nextStat=input.end;if(mode==6)sound.enabled=false;if(mode==7)sound.song=12;
            bool rejected=false;try{airTitleResetPrefix(input,sound,[](auto...){},[](auto...){},[](auto...){ });}catch(const std::runtime_error&){rejected=true;}
            require(rejected,"Unowned reset entries must reject");sound.enabled=true;sound.song=13;
        }
        printf("PASS: %d native title-reset assertions.\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}
}
