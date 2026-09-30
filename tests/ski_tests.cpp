#include "ski.h"
#include <algorithm>
#include <memory>
#include <cstdio>
#include <stdexcept>
namespace ticd {
// Predictive controller changes only Button inputs in the tested run.
namespace {
int ycoord(int y){return y>65000?y-65536:y;}
double score(const SkiGame& g){
 auto& p=g.entities[0];int y=ycoord(p.y);if((g.resultFlags&1)||(g.result&1)){return ((g.resultFlags|g.result)&2)?1e9:-1e9;}

 int need=g.assets.levels[g.difficulty].quota/2;double value=std::min(g.collected,need)*20000+y*.6;
 if(p.handler==SkiHandler::Crash||p.handler==SkiHandler::Return)value-=2000;
 if(g.collected<need){double target=1e9;
  for(auto& e:g.entities)if(e.alive&&(e.collision==16||e.collision==17)&&ycoord(e.y)>=y-256){
   auto& m=g.assets.frames[e.frame].meta;auto& pm=g.assets.frames[p.frame].meta;
   int tx=e.x+(static_cast<int8_t>(m[0])+m[2]+m[4]/2)*16, px=p.x+(static_cast<int8_t>(pm[0])+pm[2]+pm[4]/2)*16;
   target=std::min(target, std::abs(tx-px)*1.8+std::max(0,ycoord(e.y)-y)*.25);
  }
  if(target<1e9)value-=target;
 }
 return value;
}
struct Node{std::unique_ptr<SkiGame> game;int first;double value;};
int skiInput(const SkiGame& initial){
 std::vector<Node> beam;beam.push_back({std::make_unique<SkiGame>(initial),0,0});int inputs[]={0,Left,Right,Down,A,A|Left,A|Right};
 for(int depth=0;depth<3;++depth){std::vector<Node> next;
  for(const auto& node:beam)for(int input:inputs){auto g=std::make_unique<SkiGame>(*node.game);for(int f=0;f<24&&!g->result;++f)g->step(input);
   next.push_back({std::move(g),depth?node.first:input,0});next.back().value=score(*next.back().game);}
  std::stable_sort(next.begin(),next.end(),[](const Node&a,const Node&b){return a.value>b.value;});if(next.size()>8)next.resize(8);beam=std::move(next);
 }return beam[0].first;
}
}
int runSkiTests(const SkiAssets& assets,const Assets& shared){
    FILE* log=fopen("ski-test.txt","w");if(!log)return 2;int count=0;
    auto require=[&](bool value,const char* message){++count;if(!value)throw std::runtime_error(message);};
    try{
        SkiGame g(assets,shared);g.start(0);
        require(g.cameraX==0x6400&&g.cameraY==0&&g.entities[0].x==0x6800&&g.entities[0].y==0xff00,"Original Ski camera and player origin");
        require(g.remaining==30&&g.needed==15&&g.seconds==80,"Original Ski easy counters");
        g.step(0);require(g.entities[0].handler==SkiHandler::Play&&g.secondTicks==0,"Ski intro changes state without falling into gameplay");
        g.placements.clear();g.step(0);require(g.entities[0].y==0xff00&&g.entities[0].params[2]==1,"Movement precedes velocity approach");
        g.step(0);require(g.entities[0].y==0xff01&&g.entities[0].params[2]==2,"Initial downward acceleration");
        g.start(0);g.held=B;g.movePlayer();require(g.entities[0].params[2]==2,"B doubles approach steps without replacing the speed target");
        g.held=Left;g.input();require(g.entities[0].params[0]==1&&!g.entities[0].animDone,"Left starts a positive-angle turn animation");
        g.input();require(g.entities[0].params[0]==1,"Active turn animation gates another turn");
        g.entities[0].animDone=true;g.input();require(g.entities[0].params[0]==2,"Second left turn reaches maximum angle");
        g.entities[0].animDone=true;g.held=Right;g.input();require(g.entities[0].params[0]==1,"Right reduces current left angle");
        g.entities[0].animDone=true;g.input();require(g.entities[0].params[0]==255,"Direction change skips neutral angle");
        g.entities[0].animDone=true;g.held=Down;g.input();require(g.entities[0].params[0]==0,"Down starts the return-to-straight animation");
        g.start(0);g.jump();require(g.jumpVelocity==-64&&g.entities[0].frame==7&&g.entities[1].kind==44,"Jump creates original shadow and vertical impulse");
        int y=g.entities[0].y;g.update(0);require(g.entities[0].y==((y-8)&65535)&&g.jumpVelocity==-62,"Jump combines half impulse with 24-unit forward motion");
        g.start(0);int flag=g.spawn(38,0,0);g.collideWith(flag);g.collideWith(flag);
        require(g.money==10&&g.remaining==29&&g.needed==14&&g.collected==1,"Flag collection scores once and reduces both counters");
        flag=g.spawn(36,0,0);g.collideWith(flag);require(g.money==15&&g.collected==2,"Second flag type awards five");
        for(int collected:{0,14,15,30}){
            g.start(0);g.remaining=30-collected;g.needed=(15-collected)&255;g.entities[0].y=120*256;
            g.finishLine();require(g.resultFlags==(collected>=15?(collected==30?7:3):1),"Finish requires at least half the flags; every flag gives perfect result");
            require(g.finishTimer==63,"Ski result delay starts on finish tick");
        }
        g.start(0);g.entities[0].y=114*256;g.depth();require(g.finishZone&&(g.entities[0].flags&128),"Entering finish tunnel sets original background priority");
        g.entities[0].y=117*256;g.depth();require(g.finishZone&&!(g.entities[0].flags&128),"Finish collision suppression persists after tunnel priority ends");
        g.start(0);g.entities[0].x+=7;g.entities[0].y=1007;int trap=g.spawn(40,0,0);g.collideWith(trap);
        require(g.entities[0].handler==SkiHandler::Crash&&g.returnY==992&&!g.entities[trap].alive,"Trap stores pixel-aligned return position and consumes object");
        for(int d=0;d<4;++d)for(int pattern=0;pattern<3;++pattern){
            g.start(d);for(int t=0;t<14000&&!g.result;++t){
                int input=pattern==0?0:pattern==1?B:((t/150)%2?Left:Right)|((t%180==0)?A:0);
                g.step(input);require(g.animationFaults==0,"Ski replay animation graph valid");
                for(const auto& e:g.entities)if(e.alive)require(e.frame>=0&&e.frame<39&&e.x>=0&&e.x<=65535&&e.y>=0&&e.y<=65535,"Ski replay entity bounds");
            }
            fprintf(log,"difficulty=%d pattern=%d ticks=%d flags=%02x money=%d collected=%d\n",d,pattern,g.ticks,g.result,g.money,g.collected);
            require(g.result!=0,"Ski replay reaches terminal result");g.render();for(int shade:g.screen)require(shade>=0&&shade<4,"Ski palette bounds");
        }
        for(int d=0;d<4;++d){
            g.start(d);std::vector<int> replay;
            for(int t=0;t<10000&&!g.result;t+=8){int input=skiInput(g);for(int f=0;f<8&&!g.result;++f){replay.push_back(input);g.step(input);}}
            require(g.result==3,"Input-only Ski controller reaches finish on all four difficulties");
            require(g.collected>=assets.levels[d].quota/2,"Successful Ski input replay collects the required flags");
            SkiGame replayed(assets,shared);replayed.start(d);for(int input:replay)replayed.step(input);
            require(replayed.result==g.result&&replayed.collected==g.collected&&replayed.money==g.money,"Fresh Ski replay reproduces success using only recorded buttons");
            fprintf(log,"input-only success difficulty=%d ticks=%d flags=%02x collected=%d seconds=%d\n",d,g.ticks,g.result,g.collected,g.seconds);
        }
        SkiGame secondPlayer(assets,shared);secondPlayer.start(0,1);require(secondPlayer.hudValues[0]==0xf8,"ski HUD identifies second campaign player");
        fprintf(log,"PASS: %d assertions. Native rule/replay checks; original equivalence remains unverified.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
