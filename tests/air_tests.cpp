#include "air.h"
#include <algorithm>
#include <memory>
#include <cstdio>
#include <stdexcept>

namespace ticd {
namespace {
// Test pilot observes native state; only ordinary buttons reach the actual run.
double airScore(const AirGame& g){
 auto& p=g.entities[0];if(g.resultFlags&1)return (g.resultFlags&2)?1e9:-1e9;
 int need=g.assets.levels[g.difficulty].quota/2+1;
 double value=std::min<int>(p.params[1],need)*20000-p.y*.6-p.params[5]*2;
 if(p.params[1]<need){double target=1e9;
  for(auto& e:g.entities)if(e.alive&&e.collision==8&&e.y<=p.y+512){
   int dx=static_cast<int16_t>(e.x-p.x);dx=((dx+2048)&4095)-2048;
   target=std::min(target,std::abs(dx)*1.8+std::abs(e.y-p.y)*.3);
  }
  if(target<1e9)value-=target*(g.difficulty==3?0:1);
 }
 return value;
}
struct Node{std::unique_ptr<AirGame> game;int first;double value;};
int campaignAirStart=0,campaignAirPeriod=44,campaignAirOffset=0;
int airInput(const AirGame& initial){
 if(initial.difficulty==0)return A|((initial.ticks/44)%2?Left:Right);
 std::vector<Node> beam;beam.push_back({std::make_unique<AirGame>(initial),0,0});int inputs[]={A,A|Left,A|Right,0,Left,Right,B,B|Left,B|Right};
 for(int depth=0;depth<5;++depth){std::vector<Node> next;
  for(const auto& node:beam)for(int input:inputs){auto g=std::make_unique<AirGame>(*node.game);for(int f=0;f<32&&!g->result;++f)g->step(input);
   next.push_back({std::move(g),depth?node.first:input,0});next.back().value=airScore(*next.back().game);}
  std::stable_sort(next.begin(),next.end(),[](const Node&a,const Node&b){return a.value>b.value;});if(next.size()>16)next.resize(16);beam=std::move(next);
 }return beam[0].first;
}
}

void prepareAirTestInput(const AirGame& initial){
 campaignAirStart=initial.ticks;campaignAirPeriod=44;campaignAirOffset=0;
 if(initial.difficulty)return;
 // Find an ordinary input schedule at this campaign's actual frame phase.
 // Forecast copies never alter the measured run or its frame counter.
 for(int period:{44,43,45,42,46,40,48,36,52,56,60})for(int offset=0;offset<period*2;offset+=2){
  AirGame trial(initial);for(int elapsed=0;elapsed<6000&&!trial.result;++elapsed)trial.step(A|(((elapsed+offset)/period)%2?Left:Right));
  if(trial.result&2){campaignAirPeriod=period;campaignAirOffset=offset;return;}
 }
}
int airTestInput(const AirGame& game){
 if(!game.difficulty)return A|(((((game.ticks-campaignAirStart)&65535)+campaignAirOffset)/campaignAirPeriod)%2?Left:Right);
 return airInput(game);
}
int runAirTests(const AirAssets& assets,const Assets& shared){
    FILE* log=fopen("air-test.txt","w");if(!log)return 2;
    int assertions=0;
    auto require=[&](bool ok,const char* label){++assertions;if(!ok)throw std::runtime_error(label);};
    try{
        AirGame g(assets,shared);g.start(0);
        require(g.cameraX==0x4f00&&g.cameraY==0xae80,"Original Air camera origin");
        require(g.entities[0].x==0x5300&&g.entities[0].y==0xb600,"Original Air player origin");
        require(g.seconds==40&&assets.levels[0].quota==14,"Original easy timer and quota");
        require(assets.levels[2].rows==256&&assets.levels[2].objects.size()==143,"Preserve 256-row maps without truncation");
        for(int j=0;j<40;++j)g.step(A);
        require(g.entities[0].y==0xb600-820,"Forty intro rise steps from -40 through -1");
        require(g.entities[0].handler==AirHandler::Wait&&g.entities[0].params[0]==223,"Rise falls into first countdown update");
        for(int j=0;j<222;++j)g.step(A);
        require(g.entities[0].handler==AirHandler::Wait&&g.seconds==40,"Intro does not consume stunt time");
        g.step(A);require(g.entities[0].handler==AirHandler::Play&&g.secondTicks==1,"Countdown falls into gameplay on final tick");
        int ticks=g.ticks;g.paused=true;g.step(B);require(g.ticks==ticks,"Air pause freezes all gameplay");g.paused=false;

        g.start(0);g.cameraY=0x8000;g.cameraX=0x4f00;g.entities[0].x=0x5310;g.entities[0].y=0x8580;
        g.followCamera();require(g.cameraX==0x4f01&&g.cameraY==0x8000,"Camera uses signed subpixel X error and doubled Y lead");
        g.start(0);g.tilt=2;g.speed=-20;g.lookupRate();
        require(g.rate==-16,"Top upward speed curve endpoint");
        int x=g.entities[0].x,y=g.entities[0].y;g.movePlayer();
        require(g.entities[0].x==x+32&&g.entities[0].y==y-32,"Tilt multiplies original fixed-point speed");
        require(g.entities[0].frame==2&&!(g.entities[0].flags&32),"Right tilt frame and mirror flag");
        g.entities[0].params[3]=1;g.entities[0].params[4]=static_cast<uint8_t>(-2);x=g.entities[0].x;
        g.movePlayer();require(g.entities[0].x==x-32&&g.entities[0].params[3]==0,"Final boost tick still uses stored direction");
        g.ticks=16;g.held=A;g.speed=0;g.rate=0;g.input();
        require(g.speed==0,"A acceleration and neutral-axis drag both run on tick sixteen");
        g.ticks=20;g.input();require(g.speed==-1,"A accelerates every four ticks");
        g.tilt=-1;g.held=Right;g.input();require(g.tilt==-1,"No turn when previous vertical rate is zero");
        g.tilt=0;g.rate=-1;g.lastForce=4;g.input();require(g.tilt==0,"Conveyor feedback suppresses turn input");
        g.lastForce=0;g.input();require(g.tilt==1,"Turn resumes when terrain feedback clears");

        g.start(0);g.setFrame(0,1,32);g.finishVideoTick(0,0);
        require(g.entities[0].frame==0&&g.transferRemaining==13&&g.transferState==1,"Frame request holds old display during thirteen-chunk transfer");
        g.beginVideoTick();require(g.transferRemaining==13,"Background row transfer takes priority over sprite chunks");
        g.mapTransfer=false;
        for(int n=0;n<3;++n)g.beginVideoTick();
        require(g.transferRemaining==1&&g.entities[0].frame==0,"Three resource ticks copy twelve chunks");
        g.beginVideoTick();require(g.transferState==2&&g.entities[0].frame==1&&g.entities[0].flags==32,"Completion installs requested frame and flags atomically");
        g.rate=-1;g.held=Right;g.input();require(g.tilt==0,"Turn stays blocked during completed-transfer handshake");
        g.finishVideoTick(1,32);require(g.transferState==0,"Post-update handler clears completion handshake");

        g.start(0);int frameCommand=0;
        for(int n=1;n<static_cast<int>(assets.commands.size());++n)if(assets.commands[n].op==4&&assets.commands[n].a==3){frameCommand=n;break;}
        require(frameCommand!=0,"Crash graph has original dynamic frame command");
        g.entities[0].anim=frameCommand;g.entities[0].animDone=false;g.entities[0].period=17;g.animate(0);
        require(g.entities[0].frameWaiting&&g.entities[0].anim==frameCommand,"Animation command pauses at pending frame operand");
        g.finishVideoTick(0,0);g.mapTransfer=false;g.beginVideoTick();g.animate(0);
        require(g.entities[0].frameWaiting&&g.entities[0].delay==0,"Animation delay starts after transfer, not before");
        g.beginVideoTick();g.animate(0);
        require(!g.entities[0].frameWaiting&&g.entities[0].delay==17,"Completed transfer releases animation to its delay command");

        g.start(0);g.startAnimation(0,1,true);int savedBlock=g.entities[0].anim;
        g.animate(0);g.finishVideoTick(0,0);
        require(g.entities[0].anim==savedBlock&&g.entities[0].frameWaiting&&g.pendingSound==15,"Dynamic frame yield preserves the script block preceding its sound command");
        for(int n=0;n<2;++n){g.pendingSound=-1;g.beginVideoTick();g.animate(0);
            require(g.entities[0].anim==savedBlock&&g.pendingSound==15&&g.entities[0].delay==0,"Map-priority transfer waits replay the original block's sound request without starting its delay");}
        g.mapTransfer=false;while(g.transferRemaining)g.beginVideoTick();g.pendingSound=-1;g.animate(0);
        require(!g.entities[0].frameWaiting&&g.entities[0].anim!=savedBlock&&g.entities[0].delay==8&&g.pendingSound==15,"Completed transfer reaches the delay command and only then saves the following script position");
        g.pendingSound=-1;g.animate(0);
        require(g.pendingSound==-1&&g.entities[0].delay==7,"Committed animation delay no longer replays preceding sound requests");

        g.start(0);g.speed=-8;g.probes={1,0,0,0,0,0};g.terrainBounce();
        require(g.tilt==1&&g.lastForce==12&&g.speed==-8,"Rising left contact turns right before bouncing");
        g.tilt=2;g.terrainBounce();require(g.speed==9&&g.entities[0].params[5]==16,"Maximum tilt impact adds damage and reverses upward motion");
        require(g.pendingSound==10,"Air impact queues original effect 10");
        g.probes={0,0,0,0,0,1};g.terrainBounce();require(g.speed==-4&&g.entities[0].params[5]==32,"Falling center impact selects upward bounce");
        g.entities[0].params[3]=64;g.speed=-10;g.probes={1,0,0,0,0,0};g.terrainBounce();
        require(g.speed==-10&&g.entities[0].params[3]==0&&g.entities[0].params[5]==32,"First boost collision cancels boost without damage");
        g.entities[0].params[5]=240;g.damage(16);
        require(g.resultFlags==0x21&&g.finishTimer==127&&g.entities[0].params[5]==0,"Damage byte carry triggers original failure and immediate delay tick");

        g.start(0);g.rate=1;g.held=A;g.ticks=3;g.input();
        require(g.speed==0,"Air thrust waits for the global four-update phase");
        g.ticks=4;g.input();require(g.speed==-1,"Air thrust uses the supplied global phase");
        g.start(0);g.ticks=65535;g.step(0);require(g.ticks==0,"Original global frame counter wraps at sixteen bits");

        for(int collected:{0,7,8,14}){
            g.start(0);g.placements.clear();g.speed=-8;g.entities[0].params[1]=static_cast<uint8_t>(collected);g.probes={8,0,0,0,0,0};
            g.finishGate();require(g.money==150&&g.entities[0].handler==AirHandler::FinishMotion,"Bonus gate gives 150 and enters finish motion");
            require(g.resultFlags==(collected==14?7:collected>7?3:1),"Half quota is insufficient; full quota gives perfect result");
        }
        g.start(0);g.speed=-8;g.probes={16,0,0,0,0,0};g.finishGate();require(g.money==50,"Ordinary gate gives 50");
        g.start(0);g.placements.clear();g.seconds=1;g.secondTicks=59;g.entities[0].handler=AirHandler::Play;
        g.step(0);require(g.resultFlags==0x11&&g.finishTimer==127,"Timeout starts result countdown on zero-second tick");
        for(int j=0;j<127;++j)g.step(0);require(g.result==0x11,"Timeout reaches terminal result after 128 ticks");

        g.start(0);int pickup=g.spawn(18,g.entities[0].x,g.entities[0].y);g.placements[0].active=true;g.entities[pickup].placement=0;
        g.collideWith(pickup);g.collideWith(pickup);
        require(g.money==10&&g.entities[0].params[1]==1&&g.placements[0].active,"Collected placement scores once and stays consumed");
        int falling=g.spawn(29,0,0);g.collideWith(falling);require(g.entities[falling].alive,"Falling pickup requires player crash state");
        g.entities[0].params[2]=255;g.collideWith(falling);require(!g.entities[falling].alive&&g.money==30,"Crash state can collect falling pickup");
        g.entities[0].params[2]=0;int heal=g.spawn(23,0,0);g.entities[0].params[5]=16;g.collideWith(heal);
        require(g.money==105&&g.entities[0].params[5]==0,"Healing pickup decodes BCD points and clamps damage");
        int block=g.spawn(19,0,0);g.collideWith(block);
        require(g.entities[0].params[5]==48&&g.entities[block].collision==255,"Breakable obstacle applies both impact and extra damage");
        g.start(0);int scenery=g.spawn(24,0,0,0);g.placements[0].active=true;g.updateVisibility();
        require(!g.entities[scenery].alive&&!g.placements[0].active,"Offscreen scenery frees its placement for later respawn");

        // Map lookup must wrap X every 256 pixels and Y at the 16-bit world edge.
        for(int yy=0;yy<65536;yy+=977)for(int xx=0;xx<4096;xx+=211){
            require(g.terrainAt(xx,yy)==g.terrainAt(xx+4096,yy),"Horizontal map wrap");
            require(g.tileAt(xx,yy)==g.tileAt(xx,yy+65536),"Vertical coordinate wrap");
        }
        for(int d=0;d<4;++d){
            for(int pattern=0;pattern<3;++pattern){
                g.start(d);
                for(int j=0;j<12000&&!g.result;++j){
                    int buttons=pattern==0?A:pattern==1?0:A|((j/120)%2?Left:Right);
                    g.step(buttons);
                    require(g.speed>=-20&&g.speed<=11&&g.tilt>=-2&&g.tilt<=2,"Air replay movement domain");
                    require(g.animationFaults==0,"Air replay animation graph remains valid");
                    for(const auto& e:g.entities)if(e.alive)require(e.frame>=0&&e.frame<59&&e.x>=0&&e.x<=65535&&e.y>=0&&e.y<=65535,"Air replay entity bounds");
                }
                fprintf(log,"difficulty=%d pattern=%d ticks=%d flags=%02x money=%d collected=%d\n",d,pattern,g.ticks,g.result,g.money,g.entities[0].params[1]);
                require(g.result!=0,"Air replay reaches a terminal result");
                if(d==0&&pattern==2)require(g.result==3&&g.entities[0].params[1]>7,"Easy steering replay reaches successful quota result");
                g.render();for(int shade:g.screen)require(shade>=0&&shade<4,"Air frame palette bounds");
            }
        }
        for(int d=0;d<4;++d){
            AirGame run(assets,shared);run.start(d);std::vector<int> inputs;
            while(run.ticks<10000&&!run.result){int input=airInput(run);int batch=d==0?1:8;for(int j=0;j<batch&&!run.result;++j){inputs.push_back(input);run.step(input);}}
            require((run.result&3)==3,"Air input-only controller reaches success on every difficulty");
            AirGame replay(assets,shared);replay.start(d);for(int input:inputs)replay.step(input);
            require(replay.result==run.result&&replay.money==run.money&&replay.entities[0].params[1]==run.entities[0].params[1],"Air recorded buttons reproduce completed outcome");
            require(run.animationFaults==0&&replay.animationFaults==0,"Air successful replay uses valid animation graph");
            fprintf(log,"input-only success difficulty=%d ticks=%d flags=%02x money=%d collected=%d\n",d,run.ticks,run.result,run.money,run.entities[0].params[1]);
        }
        AirGame secondPlayer(assets,shared);secondPlayer.start(0,1);require(secondPlayer.hudValues[0]==0xf8,"air HUD identifies second campaign player");
        fprintf(log,"PASS: %d assertions. Static rule checks and native replays; full original equivalence remains unverified.\n",assertions);
        fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",assertions,e.what());fclose(log);return 1;}
}
}
