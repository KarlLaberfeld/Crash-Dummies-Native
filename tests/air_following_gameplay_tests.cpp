// Synthetic handoff and unowned-work guards; no ROM or original recordings.
#include "air_following_gameplay.h"
#include <cstdio>
#include <memory>
using namespace ticd;
int main(){
    int checks=0;auto require=[&](bool value,const char* message){++checks;if(!value)throw std::runtime_error(message);};
    try{
        auto assets=std::make_unique<AirAssets>();auto shared=std::make_unique<Assets>();
        assets->definitions[0].handler=AirHandler::Intro;
        for(int difficulty=0;difficulty<4;++difficulty){assets->levels[difficulty].cameraX=0x4f00+256*difficulty;assets->levels[difficulty].cameraY=0xae80+128*difficulty;assets->levels[difficulty].seconds=40+difficulty;assets->levels[difficulty].quota=1;}
        for(int difficulty=0;difficulty<4;++difficulty)for(int player=0;player<2;++player)for(bool reverse:{false,true}){
            auto preceding=std::make_unique<AirGame>(*assets,*shared),game=std::make_unique<AirGame>(*assets,*shared);
            preceding->difficulty=difficulty;preceding->playerNumber=player;preceding->result=33;preceding->secondTicks=59;preceding->randomState=0x1200;preceding->reverseSprites=reverse;
            for(int i=0;i<16;++i){auto& e=preceding->entities[i];e.anim=20+i;e.delay=3+i;e.period=10+i;e.loop=2+i;e.loopStart=40+i;e.animDone=false;e.frameWaiting=true;}
            AirFollowingSetup state;state.stage=1;state.difficulty=difficulty;state.display=state.stat=4;state.ready=0;state.hudCursor=2;state.fadeRemaining=7;
            state.cameraX=assets->levels[difficulty].cameraX;state.cameraY=assets->levels[difficulty].cameraY;state.randomState=0xf200;
            auto& c=state.instruction.map.campaign;c.player=player;c.timing.tick=65535;c.timing.input.held=c.timing.input.previous=33;
            airFollowingAirHandoff(*game,*preceding,state);
            require(game->secondTicks==59&&game->seconds==40+difficulty,"The inherited partial second and fresh level duration have separate owners");
            require(game->ticks==65535&&game->randomState==0xf200&&game->randomState!=preceding->randomState,"Following display time and scene seed come from the native entry");
            require(game->hudCursor==2&&game->displayFadeRemaining==7&&game->mapTransfer,"The two startup displays retain their HUD/fade and map gate");
            require(game->lastMapCamera==((state.cameraY+128)&65535),"Initial map preparation retains its penultimate native world row");
            require(game->reverseSprites==reverse&&game->sprites.descending()==reverse,"Sprite allocation direction survives the result and instruction");
            require(game->held==(A|Left)&&game->previous==game->held&&!game->pressed,"Inherited held controls cannot manufacture a fresh gameplay edge");
            for(int i=0;i<16;++i){const auto& e=game->entities[i];const auto& old=preceding->entities[i];
                require(e.anim==old.anim&&e.delay==old.delay&&e.period==old.period&&e.loop==old.loop&&e.loopStart==old.loopStart,"All sixteen native animation blocks survive the actor clear");
                require(i<2?e.animDone&&!e.frameWaiting:!e.animDone&&e.frameWaiting,"Only the two newly allocated actors reset animation done/waiting flags");
            }
            require(!game->result&&game->pendingSound==-1&&!game->transferState,"Fresh actor/resource outcome is separate from inherited animation state");
            c.timing.input.previous=32;c.timing.input.pressed=1;airFollowingAirHandoff(*game,*preceding,state);
            require(game->held==(A|Left)&&game->previous==Left&&game->pressed==A,"A genuine last-display fresh edge survives the handoff");
        }
        auto preceding=std::make_unique<AirGame>(*assets,*shared),game=std::make_unique<AirGame>(*assets,*shared);
        preceding->result=33;AirFollowingSetup state;state.stage=1;state.display=state.stat=4;state.hudCursor=2;state.cameraX=assets->levels[0].cameraX;state.cameraY=assets->levels[0].cameraY;
        auto rejects=[&]{try{airFollowingAirHandoff(*game,*preceding,state);return false;}catch(const std::runtime_error&){return true;}};
        preceding->result=3;require(rejects(),"Successful Air cannot borrow retry handoff timing");preceding->result=33;
        preceding->secondTicks=60;require(rejects(),"Malformed inherited timer phase rejects");preceding->secondTicks=0;
        state.difficulty=1;require(rejects(),"An unowned difficulty change rejects");state.difficulty=0;
        state.instruction.map.campaign.player=1;require(rejects(),"A different selected player needs its shared animation-pool owner");state.instruction.map.campaign.player=0;
        state.stage=2;require(rejects(),"Ski requires its own native gameplay handoff");state.stage=1;
        state.cameraX++;require(rejects(),"Handoff cannot replace decoded level geometry with another value");state.cameraX--;
        bool alias=false;try{airFollowingAirHandoff(*preceding,*preceding,state);}catch(const std::runtime_error&){alias=true;}require(alias,"Handoff refuses to overwrite its own inheritance source");
        printf("Following Air handoff checks: %d passed (synthetic; no original parity claim)\n",checks);return 0;
    }catch(const std::exception& e){fprintf(stderr,"Following Air handoff failed after %d checks: %s\n",checks,e.what());return 1;}
}
