// Bounded native pause candidate. No original LCD/poll/work/storage input.
#include "air_pause_session.h"
#include "air_pause_lcd.h"
#include <cstdio>
using namespace ticd;
int main(int argc,char** argv){
    if(argc!=4){fprintf(stderr,"Usage: air-pause-probe native-graphics.txt bus.csv paused-buttons.txt\n");return 2;}
    try{
        std::ifstream input(argv[1]),buttons(argv[3]);
        std::ofstream bus(argv[2]),phases(std::string(argv[2])+".phases.csv"),
            storage(std::string(argv[2])+".graphics.csv"),services(std::string(argv[2])+".services.csv");
        AirClock clock;AirPauseLcd lcd;AirPauseGraphics graphics;int tick,held,previous,pending;
        if(!bus||!phases||!storage||!services||!buttons||
           !(input>>clock.now>>lcd.scrollX>>lcd.windowX>>lcd.windowY>>tick>>held>>previous>>pending))
            throw std::runtime_error("Invalid native pause prefix/outputs");
        for(auto& object:lcd.objects)if(!(input>>object.x>>object.y))throw std::runtime_error("Missing native graphics objects");
        for(auto& byte:graphics.row){int value;if(!(input>>value)||value<0||value>255)throw std::runtime_error("Missing native HUD row");byte=static_cast<unsigned char>(value);}
        int extra;if(input>>extra)throw std::runtime_error("Unexpected native graphics data");
        if(!input.eof()||lcd.scrollX<0||lcd.scrollX>255||pending!=-1)throw std::runtime_error("Invalid graphics data or unowned pending effect");
        auto assets=AirPauseAssets::load("build/pause.dat");graphics.font=assets.restoreFont;
        clock.nextStat=(clock.now/AirClock::Frame)*AirClock::Frame+AirClock::StatLine;
        clock.nextVBlank=(clock.now/AirClock::Frame)*AirClock::Frame+AirClock::VBlankLine;
        if(clock.nextStat<=clock.now)clock.nextStat+=AirClock::Frame;
        if(clock.nextVBlank<=clock.now)clock.nextVBlank+=AirClock::Frame;
        DisplayInput sampled;sampled.held=held;sampled.previous=previous;sampled.pressed=held&~previous;
        bus<<"phase,kind,address,value,cycle\n";phases<<"phase,start,end,work\n";
        services<<"service,cycle,tick,held,pressed,display,effects,music\n";
        storage<<"phase,cycle";for(int i=0;i<20;++i)storage<<",status"<<i;for(int i=0;i<128;++i)storage<<",font"<<i;storage<<'\n';
        auto display=[&](bool ready){
            int raw;if(!(buttons>>raw)||raw<0||raw>255||(raw&15)==15||ready)
                throw std::runtime_error("Missing/unsupported paused display input or gate");
            sampled.sample(raw);services<<clock.displays<<','<<clock.now<<','<<tick<<','<<sampled.held<<','<<sampled.pressed<<",160,64,60\n";
            tick=(tick+1)&65535;return 1592+160+64+60;
        };
        airPauseSession(clock,sampled,graphics,assets,display,lcd,[](bool){},
            [&](const char* name,int64_t start,int64_t end,int work){phases<<name<<','<<start<<','<<end<<','<<work<<'\n';},
            [&](const char* name,const char* kind,unsigned address,int value,int64_t time){bus<<name<<','<<kind<<','<<address<<','<<value<<','<<time<<'\n';},
            [&](const char* name,int64_t time,const AirPauseGraphics& state){storage<<name<<','<<time;for(int value:state.row)storage<<','<<value;for(int value:state.font)storage<<','<<value;storage<<'\n';});
        if(buttons>>extra)throw std::runtime_error("Unconsumed paused display samples");
        fprintf(stderr,"Native pause graphics candidate completed; full pixels/PCM, audio software state, LCD startup and production integration remain outside this probe.\n");return 0;
    }catch(const std::exception& error){fprintf(stderr,"Pause probe: %s\n",error.what());return 1;}
}
