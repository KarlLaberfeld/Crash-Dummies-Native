// Synthetic graphics owners only: no ROM, reference core or captured polls.
#include "air_pause_clock.h"
#include "air_pause_lcd.h"
#include "air_pause_session.h"
#include "air_pixels.h"
#include <cstdio>
#include <vector>

using namespace ticd;
struct Access {unsigned address;int value;int64_t time;};
int main(){
    int checks=0;
    auto require=[&](bool ok,const char* message){++checks;if(!ok)throw std::runtime_error(message);};
    try{
        auto display=[](bool){return 0;};auto available=[](int64_t){return 0;};
        for(int size:{20,128}){
            AirClock clock;clock.now=0;
            std::vector<Access> samples,reads,writes;
            auto status=[&](int64_t time){samples.push_back({0,0,time});return 0;};
            auto read=[&](int i,int64_t time){reads.push_back({unsigned(i),i&255,time});return static_cast<unsigned char>(i);};
            auto write=[&](unsigned address,unsigned char value,int64_t time){writes.push_back({address,value,time});};
            auto work=airPauseCopy(clock,size,0x8f80,display,status,read,write);
            require(work.cycles==196+104*size&&clock.now==work.cycles,"Quiet copy has complete source work without a polling allowance");
            require(work.bytes==size&&work.polls==size&&!work.failedPolls,"Each byte polls independently");
            require(samples[0].time==120&&reads[0].time==144&&writes[0].time==152,"First copy STAT/read/write sample positions are distinct");
            for(int i=0;i<size;++i){
                require(reads[i].address==unsigned(i)&&writes[i].address==0x8f80+unsigned(i)&&writes[i].value==(i&255),"Copy preserves byte order, value and destination");
                require(reads[i].time-samples[i].time==24&&writes[i].time-samples[i].time==32,"Successful copy does not collapse the three bus accesses");
                if(i)require(samples[i].time-samples[i-1].time==104,"Next byte owns the complete count/branch interval");
            }
        }
        AirClock wrapping;wrapping.now=0;std::vector<unsigned> addresses;
        auto wrap=airPauseCopy(wrapping,2,0x97ff,display,available,[](int,int64_t){return 7;},
            [&](unsigned address,unsigned char,int64_t){addresses.push_back(address);});
        require(addresses==std::vector<unsigned>({0x97ff,0x8800})&&wrap.destinationWraps==1&&wrap.cycles==408,"Destination wraps at the source graphics boundary and charges only its branch");
        AirClock blocked;blocked.now=0;std::vector<int64_t> polls;
        auto intermittent=[&](int64_t time){polls.push_back(time);return time<184?3:0;};
        auto delayed=airPauseCopy(blocked,1,0xc0a0,display,intermittent,[](int,int64_t){return 9;},[](unsigned,unsigned char,int64_t){});
        require(polls==std::vector<int64_t>({120,152,184})&&delayed.failedPolls==2&&delayed.cycles==364,"Blocked LCD samples retry after their own BIT/branch work");
        AirClock unknown;unknown.now=0;bool rejected=false;int writes=0;
        try{airPauseCopy(unknown,1,0xc0a0,display,[](int64_t){return -1;},[](int,int64_t){return 0;},[&](unsigned,unsigned char,int64_t){++writes;});}
        catch(const std::runtime_error&){rejected=true;}
        require(rejected&&!writes,"Unknown LCD ownership cannot silently supply a successful access");
        for(int size:{0,-1,65536}){
            AirClock invalid;auto before=invalid.now;rejected=false;
            try{airPauseCopy(invalid,size,0xc0a0,display,available,[](int,int64_t){return 0;},[](unsigned,unsigned char,int64_t){});}
            catch(const std::runtime_error&){rejected=true;}
            require(rejected&&invalid.now==before,"Invalid byte counts reject before time or data changes");
        }

        // A display pending during the STAT access happens after its sample.
        // Its changed mode affects the later data access, never the old branch.
        AirClock interrupted;interrupted.now=0;interrupted.nextVBlank=121;interrupted.nextStat=AirClock::Frame;
        int mode=0,value=-1,readMode=-1;bool busyGate=false;
        auto irq=[&](bool ready){busyGate=!ready;mode=3;return 0;};
        auto inFlight=airPauseCopy(interrupted,1,0xc0a0,irq,[&](int64_t){return mode;},
            [&](int,int64_t){readMode=mode;return mode==3?255:17;},[&](unsigned,unsigned char byte,int64_t){value=byte;});
        require(inFlight.polls==1&&!inFlight.failedPolls&&readMode==3&&value==255,"A retained successful poll does not certify the later VRAM read");
        require(busyGate&&interrupted.displays==1&&interrupted.now==inFlight.cycles+36,"Copy services preserve the busy resource gate and exclude IRQ work from their source total");

        AirClock sourceIrq;sourceIrq.now=0;sourceIrq.nextVBlank=147;sourceIrq.nextStat=AirClock::Frame;
        unsigned char source=17;int stored=0;
        airPauseCopy(sourceIrq,1,0xc0a0,[&](bool){source=29;return 0;},available,
            [&](int,int64_t){return source;},[&](unsigned,unsigned char byte,int64_t){stored=byte;});
        require(source==29&&stored==17,"An interrupt after the source bus read cannot replace the retained copy byte");
        AirClock writeIrq;writeIrq.now=0;writeIrq.nextVBlank=153;writeIrq.nextStat=AirClock::Frame;
        stored=0;int published=0;
        airPauseCopy(writeIrq,1,0xc0a0,[&](bool){published=stored;return 0;},available,
            [](int,int64_t){return 37;},[&](unsigned,unsigned char byte,int64_t){stored=byte;});
        require(published==37,"Destination bus write commits before its pending display publication");

        AirClock script;script.now=0;std::array<unsigned char,20> text{};
        for(unsigned i=0;i<text.size();++i)text[i]=static_cast<unsigned char>(i+1);
        polls.clear();std::vector<Access> textWrites;
        auto textWork=airPauseText(script,text,display,[&](int64_t time){polls.push_back(time);return 1;},
            [&](unsigned address,unsigned char byte,int64_t time){textWrites.push_back({address,byte,time});});
        require(textWork.cycles==4396&&script.now==4396&&textWork.bytes==20&&!textWork.failedPolls,"Identified layout covers every command and rectangle boundary");
        require(polls.front()==1244&&textWrites.front().time==1280,"Text owns a saved-byte restore between STAT and its graphics write");
        for(unsigned i=0;i<text.size();++i){
            require(textWrites[i].address==0x9c00+i&&textWrites[i].value==int(i+1)&&textWrites[i].time-polls[i]==36,"Text writes the local rectangle with its own access times");
            if(i)require(polls[i]-polls[i-1]==136,"Rectangle count/branch and store return belong to the next text byte");
        }
        AirClock scriptRetry;scriptRetry.now=0;int attempts=0;
        auto retried=airPauseText(scriptRetry,text,display,[&](int64_t){return attempts++==0?2:0;},[](unsigned,unsigned char,int64_t){});
        require(retried.cycles==4428&&retried.polls==21&&retried.failedPolls==1,"Text retry work is derived from native status samples");
        AirClock invalidAccess;auto unchanged=invalidAccess.now;rejected=false;
        try{invalidAccess.accessWork(8,9,[]{},display,false);}catch(const std::runtime_error&){rejected=true;}
        require(rejected&&invalidAccess.now==unchanged,"Invalid bus positions reject without clock mutation");
        AirPauseLcd lcd;
        int64_t row=AirClock::Frame+456;
        require(lcd.mode(0)==-1,"Unowned LCD-enable frame rejects native status polling");
        rejected=false;try{lcd.readable(0);}catch(const std::runtime_error&){rejected=true;}
        require(rejected,"First-frame read accessibility cannot be inferred from steady-frame status");
        require(lcd.mode(row+76)==2&&lcd.mode(row+77)==3,"Bounded post-counter-wait owner distinguishes the inclusive independent status edge");
        require(!lcd.readable(row+76)&&lcd.writable(row+76),"Read and write accessibility have distinct late-OAM edges");
        require(lcd.mode(row+248)==3&&lcd.mode(row+249)==0&&lcd.readable(row+249),"Pixel completion releases the independent candidate's graphics access");
        require(lcd.mode(row+80)==lcd.mode(row+80+AirClock::Frame),"Steady graphics progress independently of game updates");
        require(lcd.mode(AirClock::Frame+144*456)==1,"Blanking lines permit graphics polling without pixel transfer");
        lcd.objects[0]={40,28};lcd.objects[1]={48,28};
        require(lcd.transferEnd(15)==278&&lcd.transferEnd(28)==256,"Visible native geometry owns its line-specific transfer penalties");
        lcd.objects[1].x=41;
        require(lcd.transferEnd(15)==273,"Objects sharing a background tile avoid a second fetch wait");
        lcd.objects[0].x=41;lcd.objects[1].x=40;
        require(lcd.transferEnd(15)==273,"Horizontal fetch order uses coordinates rather than allocation order");
        lcd.objects[0].x=0;lcd.objects[1].y=0;
        require(lcd.transferEnd(15)==267,"A selected object at X zero owns the documented special fetch");
        lcd.objects[0].x=168;
        require(lcd.transferEnd(15)==256,"Objects beyond the visible right edge use selection slots without tile fetching");
        for(auto& object:lcd.objects)object={168,28};lcd.objects[10]={40,28};
        require(lcd.transferEnd(15)==256,"The first ten OAM selections retain priority over a later visible object");
        lcd.objects={};lcd.scrollX=3;
        require(lcd.transferEnd(15)==259&&lcd.transferEnd(136)==265,"Scroll and enabled window transfer stalls have independent owners");
        lcd.windowEnabled=false;
        require(lcd.transferEnd(136)==259,"Disabled window leaves only the native scroll stall");
        lcd.windowEnabled=true;lcd.windowX=166;
        require(lcd.transferEnd(136)==-1,"Unsupported special window edge cannot provide readiness");
        lcd.windowX=7;lcd.objects[0]={40,144};
        require(lcd.mode(AirClock::Frame+135*456+100)==-1,"Line-135 object cancellation requires its own fetch boundary");
        lcd.enabled=false;
        require(lcd.mode(0)==0&&lcd.readable(0)&&lcd.writable(0),"LCD off grants immediate access without a guessed first-frame phase");
        AirClock sessionClock;sessionClock.now=AirClock::Frame+44;
        sessionClock.nextStat+=AirClock::Frame;sessionClock.nextVBlank+=AirClock::Frame;
        AirPauseAssets sessionAssets;AirPauseGraphics sessionGraphics;
        for(int i=0;i<20;++i){sessionAssets.text[i]=static_cast<unsigned char>(i+30);sessionGraphics.row[i]=static_cast<unsigned char>(i+90);}
        for(int i=0;i<128;++i){sessionAssets.font[i]=static_cast<unsigned char>(i);sessionAssets.restoreFont[i]=static_cast<unsigned char>(255-i);}
        sessionGraphics.font=sessionAssets.restoreFont;auto initialRow=sessionGraphics.row;
        DisplayInput sessionInput;sessionInput.sample(8);int sampleCount=0;bool audioPaused=false;
        AirPauseLcd sessionLcd;std::vector<std::string> snapshots,phaseNames;
        airPauseSession(sessionClock,sessionInput,sessionGraphics,sessionAssets,[&](bool ready){
            require(!ready&&audioPaused,"Counter waits retain pause audio and the busy graphics resource gate");
            sessionInput.sample(++sampleCount==1?0:8);return 1876;
        },sessionLcd,[&](bool value){audioPaused=value;},
        [&](const char* name,int64_t,int64_t,int){phaseNames.emplace_back(name);},
        [](const char*,const char*,unsigned,int,int64_t){},
        [&](const char* name,int64_t,const AirPauseGraphics& state){
            snapshots.emplace_back(name);
            if(std::string(name)=="wait")require(state.row==sessionAssets.text&&state.font==sessionAssets.font,"Session publishes its local text and pause font before waiting");
        });
        require(sampleCount==2&&!audioPaused&&sessionInput.pressed==8,"Session resumes on its own fresh input edge and restores the native audio owner");
        require(sessionGraphics.row==initialRow&&sessionGraphics.font==sessionAssets.restoreFont,"Shared session restores the retained row and original font");
        require(snapshots==std::vector<std::string>({"enter","wait","restoreAudio"}),"Session storage observations cover entry, visible pause and restoration");
        require(phaseNames==std::vector<std::string>({"copy0","copy1","script","wait","wake","wait","wake","copy2","copy3","restoreAudio","return"}),"Shared session retains the identified copy/wait/restore order");
        AirClock startupClock;int64_t firstService=-1;
        startupClock.startup([&](bool){firstService=startupClock.now;return 12336;});
        require(firstService==32&&startupClock.now==12740,"LCD access tail precedes EI, both pending services and the ready store; HALT cannot hide the startup omission");
        SpriteLayer rowObjects(false);
        require(airLastLineObjectLimit(rowObjects,0,262)==160,"An empty final play row has no object-dependent clipping before completion");
        require(airPixelDot(rowObjects,4,135,108)==208&&airPixelDot(rowObjects,4,136,0)==102,"Play scroll and fixed status window have separate pixel clocks");
        for(int i=0;i<7;++i){rowObjects.slots[i].present=true;rowObjects.slots[i].y=143;}
        for(int i=0;i<7;++i)rowObjects.slots[i].x=std::array<int,7>{60,68,74,82,90,108,116}[i];
        require(airLastLineObjectLimit(rowObjects,76,262)==108,"Final-row fetch cancellation stops at the uncompleted object rather than drawing three late pixels");
        require(airLastLineObjectLimit(rowObjects,76,274)>108,"A later interrupted disable edge must remain distinguishable from the counter-wait owner");
        require(airPixelDot(rowObjects,76,135,107)<262&&airPixelDot(rowObjects,76,135,108)>=262,"Retained pixels precede the cancelled object's fetch cost");
        auto transparentClock=airLastLineObjectLimit(rowObjects,76,262);rowObjects.slots[6].colors.fill(3);
        require(airLastLineObjectLimit(rowObjects,76,262)==transparentClock,"Fetch work depends on selected geometry, including transparent pieces, not visible pixel colors");
        SpriteLayer selectedLimit(false);
        for(int i=0;i<10;++i)selectedLimit.slots[i]={true,168,143,0,{}};
        selectedLimit.slots[10]={true,116,143,0,{}};
        require(airLastLineObjectLimit(selectedLimit,0,262)==160,"Offscreen objects retain first-ten selection priority without a visible fetch stall");
        require(airPaletteSampleOffset(0)==14&&airPaletteSampleOffset(2)==34&&airPaletteSampleOffset(1)==62,"Three source palette writes own separate bus times");
        rejected=false;try{airPaletteSampleOffset(3);}catch(const std::runtime_error&){rejected=true;}
        require(rejected,"Unknown palette ownership cannot be projected as background");
        int64_t disable=0;bool waited=false;AirClock observed;observed.now=AirClock::Frame+44;
        observed.nextStat+=AirClock::Frame;observed.nextVBlank+=AirClock::Frame;
        observed.objectDisable=[&](int64_t time,AirIrqOwner owner){disable=time;waited=owner==AirIrqOwner::CounterWait;};
        observed.wait(display);
        require(waited&&disable==AirClock::Frame+AirClock::StatLine+254,"Counter-wait STAT observer exposes the identified LCD write without adding source work");
        for(int protectedCost:{192,140})for(int offset:{4,128,protectedCost-4,protectedCost,protectedCost+8}){
            int follower=protectedCost==192?12:16;
            AirClock protectedClock;protectedClock.now=0;
            protectedClock.nextVBlank=offset;protectedClock.nextStat=AirClock::Frame;
            int64_t vector=-1;AirIrqOwner owner=AirIrqOwner::Unqualified;bool restored=false,observedRestored=false;
            protectedClock.interrupt=[&](const char*,int64_t time,AirIrqOwner value){vector=time;owner=value;};
            protectedClock.holdServices(protectedCost);
            require(protectedClock.displays==0&&protectedClock.now==protectedCost,"Protected source stores retain pending services without advancing display callbacks");
            restored=true;
            protectedClock.resumeServices(follower,[&](bool ready){observedRestored=restored&&!ready;return 100;},false);
            require(vector==protectedCost+follower+20&&owner==AirIrqOwner::ProtectedResume&&observedRestored,"Pending display observes restored state only after the identified enable follower completes");
            require(protectedClock.now==protectedCost+follower+136&&!protectedClock.servicesHeld,"Protected resume retains original active work and one complete returning service");
        }
        AirClock pendingBoth;pendingBoth.now=0;pendingBoth.nextStat=4;pendingBoth.nextVBlank=8;
        std::vector<std::string> pendingOrder;
        pendingBoth.interrupt=[&](const char* kind,int64_t,AirIrqOwner){pendingOrder.push_back(kind);};
        pendingBoth.holdServices(140);pendingBoth.resumeServices(16,[](bool){return 0;},false);
        require(pendingOrder==std::vector<std::string>({"vblank","stat"})&&pendingBoth.displays==1&&pendingBoth.statServices==1,"Both pending protected requests use display priority rather than their original deadline order");
        require(pendingBoth.now==140+16+36+324,"Pending service priority adds only the identified entry/body/return costs");
        AirClock invalidProtected;invalidProtected.holdServices(140);
        rejected=false;try{invalidProtected.work(4,display,false);}catch(const std::runtime_error&){rejected=true;}
        require(rejected,"Ordinary work cannot bypass a protected source follower");
        rejected=false;try{invalidProtected.resumeServices(8,display,false);}catch(const std::runtime_error&){rejected=true;}
        require(rejected&&invalidProtected.servicesHeld,"An unidentified enable follower retains the closed service gate and rejects");
        AirClock unqualifiedPause;unqualifiedPause.now=AirClock::Frame+44;
        unqualifiedPause.nextStat=unqualifiedPause.now+200;unqualifiedPause.nextVBlank=unqualifiedPause.now+1000;
        auto beforeUnqualified=unqualifiedPause.now;bool unqualifiedSideEffect=false;
        rejected=false;try{
            airPauseSession(unqualifiedPause,sessionInput,sessionGraphics,sessionAssets,
                [&](bool){unqualifiedSideEffect=true;return 0;},sessionLcd,
                [&](bool){unqualifiedSideEffect=true;},[](const char*,int64_t,int64_t,int){},
                [](const char*,const char*,unsigned,unsigned,int64_t){},
                [&](const char*,int64_t,const AirPauseGraphics&){unqualifiedSideEffect=true;});
        }catch(const std::runtime_error&){rejected=true;}
        require(rejected,"A request during the delayed-enable follower still needs an independent original witness");
        require(unqualifiedPause.now==beforeUnqualified&&!unqualifiedSideEffect,"Unqualified pause handoff rejects before clock/audio/graphics ownership changes");
        printf("Air pause access checks: %d passed (synthetic; no LCD/reference parity claim)\n",checks);return 0;
    }catch(const std::exception& error){fprintf(stderr,"Pause access failure after %d checks: %s\n",checks,error.what());return 1;}
}
