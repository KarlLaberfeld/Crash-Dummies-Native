#pragma once
#include "air_title_layout.h"

namespace ticd {
// Identified title geometry, including the intermediate split while its
// center closes. Source callback selectors are native raster phases only.
template<class Raster,class Write>
int airTitleRasterWork(AirClock& clock,AirTitleLayout& title,int center,int64_t start,Raster&& raster,Write&& write){
    auto& r=title.reset;const auto& t=r.timing;int phase=r.stat;
    if((center!=0&&(center<176||center>254||center%2))||r.scrollX||phase<1||phase>3||
       r.lcdc!=(phase==1?0xc3:0xfb)||title.lyc!=(phase==1?23:phase==2?(center?(23-center)&255:103):103)||
       r.scrollY!=(phase==1?0:phase==2?(center+88)&255:88))throw std::runtime_error("Unowned title raster center/compare branch");
    raster("begin",start,r.stat,r.lcdc,r.scrollY,title.lyc);int64_t operation=start+200;int extra=0;
    if(phase==1){
        operation+=20;write(operation,0xff40,r.lcdc|0x38);r.lcdc|=0x38;
        operation+=36;write(operation,0xff42,(center+88)&255);r.scrollY=(center+88)&255;
        if(center){
            operation+=56;write(operation,0xff45,(23-center)&255);title.lyc=(23-center)&255;
            operation+=24;write(operation,0xc099,2);r.stat=2;extra=160;
        }else{
            operation+=88;write(operation,0xff42,88);
            operation+=20;write(operation,0xff45,103);title.lyc=103;
            operation+=24;write(operation,0xc099,2);r.stat=2;extra=212;
        }
    }else if(phase==2&&title.lyc!=103){
        operation+=36;write(operation,0xff42,88);r.scrollY=88;
        operation+=20;write(operation,0xff45,103);title.lyc=103;
        operation+=24;write(operation,0xc099,3);r.stat=3;extra=104;
    }else{
        operation+=phase==2?52:20;write(operation,0xff40,r.lcdc&0xc7);r.lcdc&=0xc7;
        operation+=16;write(operation,0xff42,0);r.scrollY=0;
        operation+=20;write(operation,0xff45,23);title.lyc=23;
        operation+=20;write(operation,0xc099,1);r.stat=1;extra=phase==2?136:104;
    }
    const int body=248+extra;
    int64_t deadline=t.lcdEpoch+(start-t.lcdEpoch)/AirClock::Frame*AirClock::Frame+title.lyc*456;
    while(deadline<=operation)deadline+=AirClock::Frame;clock.nextStat=deadline;
    raster("end",start+body,r.stat,r.lcdc,r.scrollY,title.lyc);return body;
}
}
