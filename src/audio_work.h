#pragma once
namespace ticd {
// 0403 CALL + 3707 stop/reset. Fixed-size register/state clear and initial
// wave copy from identified assets; no music stream or recorded cost is read.
inline constexpr int audioStopWork(){
    return 92+36+(44*24-4)+24+(250*40-4)+308+(16*52-4+16)+32;
}
// 00:2475's CALL and 3714 effect setup. Only identified effect roots are
// inspected; this neither executes cartridge code nor budgets music work.
inline int audioEffectSetupWork(int pending,bool squareRoot,bool noiseRoot){
    if(pending<0)return 64;
    if(pending>=26)return -1;
    return 220+(squareRoot?252:0)+(noiseRoot?148:0);
}
}
