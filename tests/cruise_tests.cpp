#include "cruise.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <queue>
#include <set>
#include <cstdio>
#include <stdexcept>
namespace ticd {
// Path planning and forecasts generate only standard Button inputs.
// Every resulting run is replayed from scratch without modifying its state.
namespace {
constexpr int Grid=128,NX=256,NY=32;
std::vector<double> distanceField;int targetX,targetY;
void prepare(const CruiseGame& g){
 for(auto& p:g.placements)if(p.kind==60){targetX=p.x;targetY=p.y;}

 distanceField.assign(NX*NY,1e7);std::vector<bool> free(NX*NY);
 using Item=std::pair<double,int>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;
 for(int y=0;y<NY;++y)for(int x=0;x<NX;++x){int bits=0;for(auto& probe:g.assets.probes)bits|=g.terrainAt(x*Grid+probe[0],y*Grid+probe[1]);int n=y*NX+x;free[n]=!(bits&3);
 if(free[n]&&x*Grid+384>=targetX&&x*Grid+128<targetX+512&&y*Grid+384>=targetY&&y*Grid+128<targetY+256){distanceField[n]=0;queue.push({0,n});}}
 
 while(!queue.empty()){auto [dist,n]=queue.top();queue.pop();if(dist!=distanceField[n])continue;int x=n%NX,y=n/NX;
  for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx){int xx=x+dx,yy=y+dy;if((!dx&&!dy)||xx<0||xx>=NX||yy<0||yy>=NY)continue;int j=yy*NX+xx;if(!free[j])continue;double next=dist+((dx&&dy)?1.414:1.0);
   if(next<distanceField[j]){distanceField[j]=next;queue.push({next,j});}}
 }

}
double score(const CruiseGame& g){
 const auto& p=g.entities[0];if(p.handler==CruiseHandler::Success||p.handler==CruiseHandler::BeginFinish||((g.resultFlags|g.result)&2))return 1e9;
 if(p.handler==CruiseHandler::Crash||p.handler==CruiseHandler::Failure||(g.resultFlags&1)||(g.result&1))return -1e9;
 int x=p.x/Grid,y=p.y/Grid;if(x>=NX||y>=NY)return -1e8;
 double distance=1e7;
 for(int yy=std::max(0,y-2);yy<=std::min(NY-1,y+2);++yy)for(int xx=std::max(0,x-2);xx<=std::min(NX-1,x+2);++xx){
  double d=distanceField[yy*NX+xx]+std::hypot(double(p.x)/Grid-xx,double(p.y)/Grid-yy);distance=std::min(distance,d);}
 return -distance*128-std::hypot(double(p.x-targetX),double(p.y-targetY))*.05+g.seconds*.02;
}
struct Node{std::unique_ptr<CruiseGame> game;int first;double value;};
int cruiseInput(const CruiseGame& initial){
 std::vector<Node> beam;beam.push_back({std::make_unique<CruiseGame>(initial),0,0});int inputs[]={0,A,Left,Right,A|Left,A|Right};
 for(int depth=0;depth<(initial.difficulty==1?10:8);++depth){std::vector<Node> next;
  for(const auto& node:beam)for(int input:inputs){auto g=std::make_unique<CruiseGame>(*node.game);for(int f=0;f<12&&!g->result;++f)g->step(input);
   next.push_back({std::move(g),depth?node.first:input,0});next.back().value=score(*next.back().game);}
  std::stable_sort(next.begin(),next.end(),[](const Node&a,const Node&b){return a.value>b.value;});std::set<unsigned long long> seen;std::vector<Node> diverse;
  for(auto& node:next){auto& p=node.game->entities[0];unsigned long long key=(p.x/64)|((unsigned long long)(p.y/64)<<10)|((unsigned long long)p.params[0]<<17)|((unsigned long long)(p.params[1]/4)<<21)|((unsigned long long)(p.params[2]/4)<<27);
   if(seen.insert(key).second){diverse.push_back(std::move(node));if(diverse.size()==(initial.difficulty==1?64:32))break;}}
  beam=std::move(diverse);
 }return beam[0].first;
}
}
int runCruiseTests(const CruiseAssets& assets,const Assets& shared){
    FILE* log=fopen("cruise-test.txt","w");if(!log)return 2;int count=0;
    auto require=[&](bool value,const char* message){++count;if(!value)throw std::runtime_error(message);};
    try{
        CruiseGame g(assets,shared);g.start(0);
        require(g.cameraY==1920&&g.entities[0].x==1040&&g.entities[0].y==3424,"Original Cruise camera and launch origin");
        require(g.entities[0].params[0]==4&&g.entities[0].params[2]==232,"Original upward heading and launch velocity");
        for(int t=0;t<31;++t)g.step(0);require(g.introTimer==31&&g.entities[0].handler==CruiseHandler::Intro,"Launch waits 31 complete updates");
        g.step(0);require(g.introTimer==33&&g.entities[0].handler==CruiseHandler::Ignition,"Launch immediately enters ignition on update 32");
        for(int t=32;t<191;++t)g.step(0);require(g.entities[0].handler==CruiseHandler::Fly&&g.seconds==60,"Ignition ends without consuming gameplay timer");
        g.start(0);g.ticks=4;g.held=A;g.entities[0].params[2]=0;g.movePlayer();
        require(g.entities[0].params[2]==254&&g.entities[0].y==3422,"Upward thrust adds the original heading vector");
        g.entities[0].params[2]=240;g.movePlayer();require(g.entities[0].params[2]==238,"Negative velocity can overshoot -16 once");
        g.movePlayer();require(g.entities[0].params[2]==238,"Negative velocity stops accelerating below -16");
        g.held=0;g.movePlayer();require(g.entities[0].params[2]==239,"Gravity approaches +8 when thrust is released");
        g.start(0);int spring=g.spawn(63,0,0,0);g.collideWith(spring);
        require(g.money==50&&g.entities[spring].collision==37,"Spring awards fifty and changes its collision during compression");
        g.reward(spring,50);require(g.money==50,"Placement rewards cannot repeat");
        for(int angle:{4,12}){g.start(0);int target=g.spawn(60,0,0);g.entities[0].params[0]=angle;g.collideWith(target);
            require(g.resultFlags==(angle==12?0x27:0x23),"Target differentiates downward perfect hit");
            for(int t=0;t<500&&!g.result;++t)g.step(0);require(g.result==(angle==12?0x27:0x23),"Target animation finishes with original success result");}
        g.start(0);int bonus=g.spawn(65,0,0);g.collideWith(bonus);require(g.extraLives==1&&!g.entities[bonus].alive,"Bonus actor awards an extra life");
        for(int d=0;d<4;++d)for(int pattern=0;pattern<3;++pattern){
            g.start(d);for(int t=0;t<8000&&!g.result;++t){int input=pattern==0?0:pattern==1?A:A|((t/120)%2?Left:Right);g.step(input);
                require(g.animationFaults==0,"Cruise replay animation graph valid");
                for(const auto& e:g.entities)if(e.alive)require(e.frame>=0&&e.frame<42&&e.x>=0&&e.x<=65535&&e.y>=0&&e.y<=65535,"Cruise replay entity bounds");
            }
            fprintf(log,"difficulty=%d pattern=%d ticks=%d flags=%02x money=%d\n",d,pattern,g.ticks,g.result,g.money);
            require(g.result!=0,"Cruise replay reaches terminal result");g.render();for(int shade:g.screen)require(shade>=0&&shade<4,"Cruise palette bounds");
        }
        for(int d=0;d<4;++d){
            g.start(d);prepare(g);std::vector<int> replay;
            for(int t=0;t<5000&&!g.result;t+=4){int input=g.entities[0].handler==CruiseHandler::Fly?cruiseInput(g):0;
                for(int f=0;f<4&&!g.result;++f){replay.push_back(input);g.step(input);}}
            require((g.result&3)==3,"Input-only Cruise planner reaches target on all difficulties");
            require(g.seconds>0&&g.animationFaults==0,"Successful Cruise route has time remaining and valid animations");
            CruiseGame replayed(assets,shared);replayed.start(d);for(int input:replay)replayed.step(input);
            require(replayed.result==g.result&&replayed.money==g.money&&replayed.seconds==g.seconds,"Fresh Cruise replay reproduces success using recorded buttons");
            fprintf(log,"input-only success difficulty=%d ticks=%d flags=%02x money=%d seconds=%d\n",d,g.ticks,g.result,g.money,g.seconds);
        }
        CruiseGame secondPlayer(assets,shared);secondPlayer.start(0,1);require(secondPlayer.hudValues[0]==0xf8,"cruise HUD identifies second campaign player");
        fprintf(log,"PASS: %d assertions. Native rule/replay checks; original equivalence remains unverified.\n",count);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",count,e.what());fclose(log);return 1;}
}
}
