// Native two-pass page clear, right-edge readiness and unskippable reopening.
#include "air_title_page.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);};
    try{
        AirPauseLcd lcd;lcd.windowX=166;lcd.objectHeight=8;
        require(lcd.transferEnd(136)==-1,"Default special window edge remains unowned");lcd.titleRightEdge=true;
        require(lcd.transferEnd(136)==256,"Qualified DMG title edge does not extend visible transfer");
        lcd.scrollX=1;require(lcd.transferEnd(136)==-1,"Right-edge title owner cannot gain horizontal scroll");lcd.scrollX=0;
        lcd.objectHeight=16;require(lcd.transferEnd(136)==-1,"Right-edge title owner requires eight-pixel empty OAM");lcd.objectHeight=8;
        lcd.objects[0].x=1;require(lcd.transferEnd(136)==-1,"Right-edge title owner cannot discard unknown object geometry");lcd.objects={};
        lcd.windowX=167;require(lcd.transferEnd(136)==-1,"Other special window edges remain unowned");
        AudioAssets audio;auto ui=std::make_unique<UiAssets>();
        for(int i=0;i<1024;++i)ui->titleMaps[0][i]=(i*17)&255;
        AirTitleClose close;close.center=176;close.steps=40;auto& l=close.fade.layout;auto& r=l.reset;auto& t=r.timing;
        l.windowX=166;l.windowY=72;l.lyc=23;r.servicesMasked=false;r.pendingRequests=0;r.lcdc=0xc3;r.stat=1;
        r.window.fill(19);r.background.fill(23);t.lcdEpoch=1000000;t.end=t.lcdEpoch+72*70224+144*456+4000;
        t.nextStat=t.lcdEpoch+73*70224+23*456;t.nextVBlank=t.lcdEpoch+73*70224+144*456;t.displays=620;t.stats=731;t.countdown=54;t.tick=65520;t.input={33,33,0};
        for(int held:{0,33,64}){NativeAudio sound(audio);sound.enabled=true;sound.song=1;sound.measureWork=true;
            int cells=0,samples=0,polls=0,busy=0,ready=0,waits=0;std::vector<int> writes;
            auto page=airTitlePage(close,sound,*ui,
                [&](const char* name,int64_t,const AirTitlePage& p){if(std::string(name)=="openWait")++waits;require(p.close.fade.layout.reset.timing.countdown==54,"UI work must preserve the result countdown");},
                [&](unsigned index,int64_t,int,int,int work,int,int,const DisplayInput& input){require(index==unsigned(620+samples-1)&&work==116&&input.held==held,"Display/input ownership continues through VRAM waits and reopening");},
                [](auto...){},[](auto...){},[&](int64_t,int mode){require(mode>=0&&mode<=3,"Only qualified LCD readiness modes enter polling");++polls;if(mode&2)++busy;else ++ready;},
                [&](int64_t,int address,int value){if(address>=0x9800&&address<0xa000){++cells;writes.push_back(value);}},[&]{++samples;return held;});
            require(cells==840&&ready==840&&polls==busy+ready&&busy>0,"Both clears and every rectangle cell have independent readiness");
            require(page.cleared==2&&page.rows==10&&page.opened==40&&waits==40,"No held action shortens page composition or reopening");
            require(page.close.center==0&&page.close.fade.layout.windowY==112,"Reopening restores exact independent center/window values");
            for(int i=0;i<640;++i)require(writes[i]==0,"Both complete clears retain zero stores");
            const auto& out=page.close.fade.layout.reset;
            for(int i=0;i<1024;++i){int value=19;if(i>=448&&i<768)value=(i%32)<20?ui->titleMaps[0][i]:0;
                require(out.window[i]==value&&out.background[i]==23,"Rectangle installation retains cleared padding and unrelated maps");}
            require(out.timing.displays==620+samples&&out.timing.tick==((65520+samples)&65535)&&sound.ticks==unsigned(samples)&&sound.song==1,"Page output inherits actual display/audio counts");
        }
        for(int mode=0;mode<5;++mode){auto bad=close;NativeAudio sound(audio);sound.enabled=true;sound.song=1;sound.measureWork=true;
            if(mode==0)bad.center=178;if(mode==1)bad.fade.layout.windowX=165;if(mode==2)bad.fade.layout.reset.objects[0]=1;if(mode==3)sound.song=13;
            bool rejected=false;try{airTitlePage(bad,sound,*ui,[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[](auto...){},[mode]{return mode==4?15:0;});}catch(const std::runtime_error&){rejected=true;}
            require(rejected,"Unowned geometry/OAM/song/reset input rejects");}
        printf("PASS: %d native title-page assertions.\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"FAIL after %d checks: %s\n",checks,e.what());return 1;}
}
