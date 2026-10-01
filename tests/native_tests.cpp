#include "game.h"
#include "campaign.h"
#include <algorithm>
#include <memory>
#include <cstdio>
#include <stdexcept>

namespace ticd {
namespace {
// Forecast copies choose ordinary buttons; the measured run is never patched.
double roofScore(const Game& g){
 auto& p=g.entities[0];if(g.resultFlags&1)return (g.resultFlags&2)?1e9:-1e9;
 double value=-std::max(-1,g.breaksNeeded)*20000+p.y*.4+g.fireHits*400;
 if(p.handler==Handler::Burning)return -1e9;
 double target=1e9;
 for(auto& e:g.entities)if(e.alive&&e.y>=p.y-256&&(((e.collision==0||e.collision==1||e.collision==3||e.collision==5)&&g.breaksNeeded>=0)||e.collision==6)){
  if(e.placement>=0&&g.placements[e.placement].state)continue;
  auto& m=g.assets.frames[e.frame].meta;auto& pm=g.assets.frames[p.frame].meta;
  int tx=e.x+(static_cast<int8_t>(m[0])+m[2]+m[4]/2)*16,px=p.x+(static_cast<int8_t>(pm[0])+pm[2]+pm[4]/2)*16;
  target=std::min(target,std::abs(tx-px)*2.+std::max(0,e.y-p.y)*.3);
 }
 if(target<1e9)value-=target;
 if(g.targetReached)value+=50000;
 return value;
}
struct Node{std::unique_ptr<Game> game;int first;double value;};
int roofInput(const Game& initial){
 if(!initial.launched)return A;
 std::vector<Node> beam;beam.push_back({std::make_unique<Game>(initial),0,0});int inputs[]={0,Left,Right,Down,Down|Left,Down|Right,Up,Up|Left,Up|Right,A};
 for(int depth=0;depth<4;++depth){std::vector<Node> next;
  for(const auto& node:beam)for(int input:inputs){auto g=std::make_unique<Game>(*node.game);for(int f=0;f<24&&!g->result;++f)g->step(input);
   next.push_back({std::move(g),depth?node.first:input,0});next.back().value=roofScore(*next.back().game);}
  std::stable_sort(next.begin(),next.end(),[](const Node&a,const Node&b){return a.value>b.value;});if(next.size()>12)next.resize(12);beam=std::move(next);
 }return beam[0].first;
}
}

int roofTestInput(const Game& game){return roofInput(game);}
int runSelfTests(const Assets& assets) {
    FILE* log=fopen("self-test.txt","w");if(!log)return 2;
    int assertions=0;
    auto require=[&](bool ok,const char* message){++assertions;if(!ok)throw std::runtime_error(message);};
    try {
        Frame collisionFrame;collisionFrame.meta={254,253,2,3,8,16,0,0};
        auto bounds=spriteBounds(collisionFrame,31,47,15,15);
        require(bounds==SpriteBounds{1,9,2,18},"Collision quantizes camera and position independently");
        bounds=spriteBounds(collisionFrame,250*16,250*16,0,0);
        require(bounds==SpriteBounds{250,2,250,10},"Collision far edges retain original byte overflow");
        require(!spriteOverlap(bounds,SpriteBounds{250,255,250,255}),"Wrapped rectangle does not become a conventional interval");
        require(spriteOverlap(SpriteBounds{10,20,10,20},SpriteBounds{20,30,20,30}),"Original collision includes far-edge contact");
        require(!spriteOverlap(SpriteBounds{20,30,20,30},SpriteBounds{10,20,10,20}),"Original collision excludes near-edge contact asymmetrically");
        {
            auto fixture=std::make_unique<Assets>(assets);auto& frame=fixture->frames[0];frame.meta={};
            SpritePiece piece;piece.colors.fill(3);frame.pieces.assign(40,piece);
            Game scene(*fixture);scene.start(0);scene.entities={};scene.camera=0;
            scene.entities[0].alive=true;scene.entities[0].frame=0;scene.entities[0].x=0x1000;scene.entities[0].y=320;
            scene.entities[1].alive=true;scene.entities[1].frame=0;scene.entities[1].x=0x1000;scene.entities[1].y=10000;scene.entities[1].flags=16;
            scene.updateVisibility();require(scene.entities[1].alive,"Full sprite list stops later entity visibility/removal work");
            frame.pieces.resize(1);scene.updateVisibility();require(!scene.entities[1].alive,"Available sprite capacity allows later offscreen removal");
            scene.render();auto before=scene.screen;scene.entities[0].x+=160;scene.render();
            require(scene.screen==before,"Repaint consumes the stored sprite list rather than changed entity state");
            scene.updateVisibility();scene.render();require(scene.screen!=before,"Next visibility pass publishes changed sprite positions");
            scene.ticks=0;bool oldDirection=scene.reverseSprites;scene.updateVisibility();
            require(scene.reverseSprites!=oldDirection,"Slot direction toggles per visibility pass independently of the global frame value");
        }
        require(assets.levels[0].height==1888,"Easy map height");
        require(assets.levels[0].objects.size()==36,"Easy placement count");
        require(assets.levels[3].objects.size()==46,"Very hard placement count");
        Game g(assets);g.start(0);
        require(g.entities[0].x==0x1290&&g.entities[0].y==0x150,"Original player origin");
        Entity p;p.x=0x1040;p.vx=-10;p.vy=24;p.y=0;
        g.moveFalling(p);require(p.x==0x1040&&p.y==24,"Left clamp / fixed point fall");
        p.x=0x1880;p.vx=10;g.moveFalling(p);require(p.x==0x1880,"Right clamp");
        p.vy=-41;p.pose=24;for(int i=0;i<65;++i)g.gravity(p);require(p.vy==24,"Bounce gravity converges");
        g.render(false);auto beforePause=g.screen;
        int unchanged=g.ticks;g.paused=true;g.step(A);require(g.ticks==unchanged,"Pause freezes simulation");
        g.render(false);require(g.screen==beforePause,"Campaign renderer preserves the paused scene without the development overlay");
        g.render();require(g.screen!=beforePause,"Development mode retains its own pause help overlay");g.paused=false;
        g.entities[0].pose=28;g.entities[0].vy=28;
        int awning=g.spawn(3,0x1400,0x1000,0);g.placements[0].state=0;
        g.collideWith(0,awning);require(g.placements[0].state==5&&g.money==10,"Head-first awning break");
        int remaining=g.remaining;g.collideWith(0,awning);require(g.remaining==remaining,"Broken awning cannot score twice");
        g.start(0);int balcony=g.spawn(8,0x1400,0x1000,0);g.entities[0].pose=24;g.collideWith(0,balcony);
        require(g.entities[0].vy==-4&&g.money==5&&g.placements[0].state==1,"Neutral balcony break from 01:5ef3");
        require(g.pendingSound==3,"Balcony break queues original effect 3");
        g.start(0);int target=g.spawn(14,0x1400,0x1000);g.collideWith(0,target);
        require(g.targetReached&&g.pendingResult==0&&g.money==100&&!g.entities[target].alive,"Target flags landing without prematurely choosing result");
        g.start(0);awning=g.spawn(3,0x1400,0x1000,0);
        g.entities[0].pose=28;g.entities[0].vy=-10;g.collideWith(0,awning);
        require(g.placements[0].state==5,"Diving breaks awning even while rising (01:5c8b)");
        g.start(0);awning=g.spawn(3,0x1400,0x1000,0);
        g.entities[0].pose=24;g.entities[0].vy=-10;g.collideWith(0,awning);
        require(g.placements[0].state==0,"Neutral upward contact does not damage awning");
        for(int hit=0;hit<4;++hit){
            g.entities[0].vy=24;g.collideWith(0,awning);
            require(g.entities[0].vy==-41+hit*4,"Original neutral bounce velocity sequence");
        }
        g.entities[0].vy=24;g.collideWith(0,awning);
        require(g.placements[0].state==5&&g.money==13,"Four bounces then fifth-hit break");

        // Contact removes a placement permanently; visibility eviction permits
        // respawning only for flagged scenery (00:1c91 / 00:3da5).
        g.start(0);target=g.spawn(14,0x1400,0x1000,0);g.placements[0].active=true;
        g.collideWith(0,target);require(g.placements[0].active,"Collected target cannot respawn");
        g.start(0);g.camera=0;awning=g.spawn(3,0x1400,0x4000,0);g.placements[0].active=true;
        g.updateVisibility();require(!g.entities[awning].alive&&!g.placements[0].active,"Offscreen scenery recycles placement");
        g.start(0);g.camera=0;g.entities[0].frame=9;g.entities[0].x=0x1200;g.entities[0].y=152*16;
        g.updateVisibility();require(!g.entities[0].offscreen,"Original lower visibility boundary is inclusive");
        g.entities[0].y+=16;g.updateVisibility();require(g.entities[0].offscreen,"Original lower visibility boundary + one pixel");

        // Landing uses the original result bitfield and body-piece scripts.
        const int landing=(assets.levels[0].height-32)*16;
        for(int allObjects=0;allObjects<2;++allObjects){
            g.start(0);g.placements.clear();g.camera=landing-100*16;
            g.targetReached=true;g.breaksNeeded=-1;g.remaining=allObjects?0:1;
            g.entities[0].y=landing+17;g.land(0);
            require(g.entities[0].y==landing+256&&g.entities[0].frame==29,"Landing snaps to next tile row");
            require(g.entities[0].handler==Handler::Idle&&g.result==0&&g.finishTimer==64,"Target landing waits for body-piece animation");
            require(g.resultFlags==(allObjects?7:3),"Perfect result requires every object");
            for(int n=0;n<300&&!g.result;++n)g.step(0);
            require(g.result==3,"Body-piece completion drives delayed success");
        }
        g.start(0);g.targetReached=true;g.breaksNeeded=0;g.entities[0].y=landing;g.land(0);
        require(g.resultFlags==0x81&&g.pendingResult==5,"Ten breaks are insufficient; threshold is eleven");
        g.start(0);g.entities[0].pose=28;g.entities[0].y=landing;g.land(0);
        require(g.entities[0].handler==Handler::Animation&&g.finishTimer==64,"Head-first miss plays impact sequence before result delay");
        g.placements.clear();for(int n=0;n<1000&&!g.result;++n)g.step(0);
        require(g.result==1,"Head-first impact sequence reaches failure");
        g.start(0);g.entities[0].pose=24;g.entities[0].y=landing;g.land(0);
        require(g.entities[0].frame==25&&g.finishTimer==63,"Neutral miss starts countdown on same tick");

        g.start(0);g.entities[0].handler=Handler::Bounce;g.entities[0].y=landing;
        g.seconds=0;g.update(0);require(g.entities[0].handler==Handler::Bounce,"Bounce routine does not run main-fall landing or timeout checks");
        g.start(0);g.entities[0].handler=Handler::Falling;g.entities[0].frame=9;g.entities[0].y=1000;
        g.seconds=1;g.secondTicks=59;g.update(0);
        require(g.seconds==0&&g.entities[0].handler==Handler::Timeout&&g.entities[0].y==969,"Timeout falls through to its movement on same tick");
        g.start(0);int plane=g.spawn(5,0x1400,0x1000);g.collideWith(0,plane);
        for(int n=0;n<63;++n)g.update(plane);
        require(g.entities[plane].handler==Handler::PlaneStun,"Plane's definition provides 64-tick stun");
        g.update(plane);require(g.entities[plane].handler==Handler::PlaneFly,"Plane resumes after original countdown");
        require(g.entities[plane].collision==255,"Plane remains non-colliding after stun");
        g.start(0);g.entities[0].handler=Handler::Falling;g.entities[0].frame=9;
        g.pressed=Up|Down;g.update(0);
        require(g.entities[0].pose==20,"Simultaneous posture presses respect animation busy check");
        g.start(0);g.camera=0;g.money=123456;g.seconds=42;g.refreshHud();
        require(g.hudValues[1]==0xf9&&g.hudValues[2]==0xfa&&g.hudValues[3]==0xfb&&g.hudValues[4]==0xfc,"Original HUD shows low four score digits");
        require(g.hudValues[5]==0xfa&&g.hudValues[6]==0xf8,"Original HUD timer digit tiles");
        require(g.hudValues[7]==0x78&&g.hudValues[12]==0x78,"Height bar full at roof");
        g.camera=54*256;g.refreshHud();
        require(g.hudValues[9]==0x78&&g.hudValues[10]==0,"Height bar half at original midpoint ratio");
        g.camera=27*256;g.refreshHud();
        require(g.hudValues[10]==0x78&&g.hudValues[11]==0x7b&&g.hudValues[12]==0,"Height bar partial tile uses original fill table");
        g.start(0);auto oldHud=g.hudMap;g.money=3456;
        for(int n=0;n<13;++n)g.tickHud();
        require(g.hudMap==oldHud,"HUD completes previous buffer before refreshing score");
        for(int n=0;n<13;++n)g.tickHud();
        require(g.hudMap[3]==0xf9&&g.hudMap[7]==0xfc,"HUD copies score through original column mapping");
        g.start(0);g.ticks=1;g.update(1);
        require(g.entities[1].x==0x19f0&&g.entities[1].y==0x90,"Odd frame advances second cloud");
        g.ticks=2;g.update(1);
        require(g.entities[1].x==0x19e0&&g.entities[1].y==-0x10,"Even frame advances first cloud");
        g.entities[1].cloudX[0]=0x0da0;g.update(1);
        require(g.entities[1].x==0x0d80&&g.entities[1].cloudX[0]==0x1a00&&g.entities[1].cloudSpeed[0]==1,"Cloud wraps its saved position after reaching original endpoint");
        for(int difficulty=0;difficulty<4;++difficulty){
            Game first(assets),second(assets);first.start(difficulty);second.start(difficulty);
            for(int i=0;i<12000;++i){
                // Complete the roof jump before steering: the original checks
                // walking first, so continuous lateral input can postpone A.
                int input=(i>450?A:0)|(i>1000?((i/180)%2?Right:Left):0)|((i/240)%3==0?Down:0);
                first.step(input);second.step(input);
                require(first.camera>=0&&first.camera<assets.levels[difficulty].height*16,"Camera stays inside level");
                if(i%60==0){first.render();second.render();require(first.screen==second.screen,"Replay determinism");}
            }
            require(first.animationFaults==0,"Animation graph terminates without invalid commands");
            require(first.launched,"Original intro reaches jump");
            require(first.result!=0,"Stunt has a terminal result");
            fprintf(log,"difficulty=%d ticks=%d result=%d money=%d animation_faults=%d\n",difficulty,first.ticks,first.result,first.money,first.animationFaults);
        }
        for(auto pair:std::array<std::array<int,2>,5>{{{1,1},{2,0x11},{3,7},{4,0x21},{5,0x81}}}){
            Game terminal(assets);terminal.start(0);terminal.resultFlags=pair[1];
            require(terminal.terminalFlags()==0,"Pending Roof result cannot settle a campaign early");
            terminal.result=pair[0];require(terminal.terminalFlags()==pair[1],"Roof development result maps to original terminal flags");
        }
        for(int d=0;d<4;++d){
            Game run(assets);run.start(d);std::vector<int> inputs;
            while(run.ticks<10000&&!run.result){int input=roofInput(run);for(int j=0;j<8&&!run.result;++j){inputs.push_back(input);run.step(input);}}
            require((run.terminalFlags()&3)==3,"Roof input-only controller reaches success on every difficulty");
            Game replay(assets);replay.start(d);for(int input:inputs)replay.step(input);
            require(replay.terminalFlags()==run.terminalFlags()&&replay.money==run.money&&replay.breaksNeeded==run.breaksNeeded,"Roof recorded buttons reproduce completed outcome");
            require(run.animationFaults==0&&replay.animationFaults==0,"Roof successful replay uses valid animation graph");
            Campaign campaign;campaign.start(false,0,d);auto settlement=campaign.settle(run.terminalFlags(),run.money,run.seconds);
            require(settlement.success&&campaign.players[0].day==1&&campaign.players[0].lives==5,"Actual Roof success advances campaign without losing a life");
            fprintf(log,"input-only success difficulty=%d ticks=%d flags=%02x money=%d breaks_needed=%d\n",d,run.ticks,run.terminalFlags(),run.money,run.breaksNeeded);
        }
        Game secondPlayer(assets);secondPlayer.start(0,1);require(secondPlayer.hudValues[0]==0xf8,"Roof HUD identifies second campaign player");
        fprintf(log,"PASS: %d assertions. These validate the native implementation, not complete equivalence to the original.\n",assertions);fclose(log);return 0;
    }catch(const std::exception& e){fprintf(log,"FAIL after %d assertions: %s\n",assertions,e.what());fclose(log);return 1;}
}
}
