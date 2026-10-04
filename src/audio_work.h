#pragma once
namespace ticd {
// 00:2475's CALL and 3714 effect setup. Only identified effect roots are
// inspected; this neither executes cartridge code nor budgets music work.
inline int audioEffectSetupWork(int pending,bool squareRoot,bool noiseRoot){
    if(pending<0)return 64;
    if(pending>=26)return -1;
    return 220+(squareRoot?252:0)+(noiseRoot?148:0);
}
}
