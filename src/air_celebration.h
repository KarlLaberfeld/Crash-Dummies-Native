#pragma once
#include <array>
#include <algorithm>
#include <cstdlib>
#include <stdexcept>

namespace ticd {
// Native state for the four identified perfect-result emitters. The shared
// random state comes from the native completed stunt, never a reference read.
struct AirCelebrationEmitter {int x=0,y=0,velocity=0,radius=0,delay=0;};
struct AirCelebration {
    std::array<AirCelebrationEmitter,4> emitters{};
    int randomState=0;
    std::array<unsigned char,160> prepared{};
    int spriteCount=0;
    static constexpr int ResetWork=328;
    void reset(int index){
        if(index<0||index>=4||randomState<0||randomState>65535)
            throw std::runtime_error("Invalid native celebration seed/emitter");
        // 1723 preserves the low byte. Both carry branches consume the same
        // 172 cycles; 157f's native field initialization consumes 156 more.
        int swapped=((randomState&255)<<8)|(randomState>>8);
        int first=(randomState-swapped)&65535;
        int value=(first-swapped-(randomState<swapped)+254)&65535;
        int lo=value&255,hi=value>>8,out=(lo-hi-(lo>=hi))&255;
        randomState=(randomState&255)|(out<<8);
        emitters[index]={(out&127)+16,143,251,0,index*16};
    }
    template<class Assets>int offset(int angle,int radius,const Assets& assets,int& work)const{
        angle&=255;bool angleNegative=angle&128,radiusNegative=radius&128;
        bool negative=angleNegative!=radiusNegative;
        int wave=assets.celebrationWave[angle&127],magnitude=radiusNegative?(-radius)&255:radius;
        int half=std::abs(wave-magnitude)/2;
        int product=(assets.celebrationProducts[std::min(wave,magnitude)+half]-assets.celebrationProducts[half])&255;
        // Identified sign and product-table branches. A negative result adds
        // the wrapper call/negation/return; no observed allowance is charged.
        work+=(angleNegative?(radiusNegative?92:72):(radiusNegative?80:60))+
              (wave>=magnitude?84:88)+(negative?48:0);
        return negative?(-product)&255:product;
    }
    template<class Assets>int advance(int tick,const Assets& assets){
        if(tick<0||tick>65535)throw std::runtime_error("Invalid celebration display counter");
        prepared.fill(0);spriteCount=0;
        // 151e's complete 160-byte list clear and four emitter dispatches.
        int work=1508;
        for(int i=0;i<4;++i){auto& emitter=emitters[i];
            if(emitter.delay){--emitter.delay;work+=144;continue;}
            if(emitter.y>=192){reset(i);work+=676;continue;}
            int oldY=emitter.y;emitter.y=(oldY+emitter.velocity)&255;
            // 1596: fixed setup, ten sprite field preparations and bank return.
            int draw=4168;int tile=assets.celebrationTiles[(emitter.radius&112)>>4];
            for(int j=0;j<10;++j){int angle=(tick+j*25)&255;
                int y=(oldY+offset(angle,emitter.radius,assets,draw))&255;
                int x=(emitter.x+offset(angle+64,emitter.radius,assets,draw))&255;
                auto base=spriteCount++*4;prepared[base]=static_cast<unsigned char>(y);
                prepared[base+1]=static_cast<unsigned char>(x);prepared[base+2]=static_cast<unsigned char>(tile);prepared[base+3]=128;
            }
            bool velocityStep=!(tick&7);if(velocityStep)emitter.velocity=(emitter.velocity+1)&255;
            bool radiusStep=!((emitter.velocity+2)&128);if(radiusStep)emitter.radius=(emitter.radius+1)&255;
            work+=468+(velocityStep?20:12)+(radiusStep?20:12)+draw;
        }
        return work;
    }
};
}
