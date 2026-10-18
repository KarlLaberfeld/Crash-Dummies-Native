#include "controller_input.h"
#include <cstdio>
int main(){
    using namespace ticd;int checks=0,failed=0;
    auto check=[&](bool ok,const char* name){++checks;if(!ok){++failed;printf("FAIL: %s\n",name);}};
    for(auto pair:{std::pair<unsigned,int>{1,Up},{2,Down},{4,Left},{8,Right},{0x1000,A},{0x2000,B},{0x10,UiStart},{0x20,UiSelect}})
        check(controllerButtons({0,pair.first})==pair.second,"button mapping");
    check(controllerButtons({0,0,7849,-7849})==0,"deadzone inclusive");
    check(controllerButtons({0,0,7850,-7850})==(Right|Down),"diagonal beyond deadzone");
    check(controllerButtons({0,0,-32768,32767})==(Left|Up),"axis extrema");
    check(controllerButtons({0,4,32767,0})==0,"opposed stick and D-pad");
    check(controllerButtons({0,15})==0,"opposed D-pad directions");
    ControllerInput pad;
    pad.update({0,0x10},true);check(!pad.held&&!pad.pressed&&!pad.armed,"held Start on attach ignored");
    pad.update({0},true);check(pad.armed,"neutral arms device");
    pad.update({0,0x10},true);check(pad.held==UiStart&&pad.pressed==UiStart,"Start rising edge");
    pad.update({0,0x10},true);check(pad.held==UiStart&&!pad.pressed,"held Start never repeats");
    pad.update({0,0x1008},true);check(pad.held==(A|Right),"simultaneous movement and action");
    pad.update({0,0x1008},false);check(!pad.held&&!pad.armed,"focus loss releases input");
    pad.update({0,0x10},true);check(!pad.held,"focus return cannot unpause while held");
    pad.update({0},true);pad.update({0,0x10},true);check(pad.pressed==UiStart,"fresh Start after focus return");
    pad.update({},true);check(pad.disconnected&&!pad.held&&!pad.armed,"disconnect releases and signals pause");
    pad.update({},true);check(!pad.disconnected,"disconnect signaled once");
    pad.update({1,0x1000},true);check(!pad.held,"replacement device must release buttons");
    pad.update({1},true);pad.update({1,0x2000},true);check(pad.pressed==B,"replacement accepts fresh action");
    pad.update({2,0x10},true);check(pad.disconnected&&!pad.held,"slot switch releases old device");
    printf("Controller checks: %d; failures: %d\n",checks,failed);return failed?1:0;
}
