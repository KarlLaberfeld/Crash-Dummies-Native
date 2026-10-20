#pragma once
#include "audio.h"
#include <ostream>
namespace ticd {
inline void airInstructionVoiceHeader(std::ostream& out){out<<"service,voice,musicCost,active,position,remaining,fixed,loopCount,transpose,noTranspose,fineTune,note,targetNote,frequency,stage,envelopeCounter,volume,releaseCounter,tableIndex,arpCounter,direction,vibratoWait,vibratoCounter,pitchWait\n";}
inline void airInstructionVoiceRows(std::ostream& out,unsigned index,const NativeAudio& sound,int music){
    for(int i=0;i<6;++i){const auto& v=sound.voices[i];out<<index<<','<<i<<','<<music<<','<<int(v.active)<<','<<v.position<<','<<v.remaining<<','<<v.fixed<<','<<v.loopCount<<','<<v.transpose<<','<<v.noTranspose<<','<<v.fineTune<<','<<v.note<<','<<v.targetNote<<','<<v.frequency<<','<<v.stage<<','<<v.envelopeCounter<<','<<v.volume<<','<<v.releaseCounter<<','<<v.tableIndex<<','<<v.arpCounter<<','<<v.direction<<','<<v.vibratoWait<<','<<v.vibratoCounter<<','<<v.pitchWait<<'\n';}
}
}
