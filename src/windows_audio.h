#pragma once
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <mmsystem.h>
#include <array>
#include <algorithm>
#include <vector>
#include <cstdint>

namespace ticd {
// Windows owns submitted buffers until WHDR_DONE. The game thread never waits
// for the device; a full queue drops output rather than blocking simulation.
class WindowsAudio {
    struct Buffer { WAVEHDR header{};std::array<int16_t,2048> samples{};bool prepared=false; };
    HWAVEOUT device=nullptr;
    std::array<Buffer,8> buffers{};
    size_t cursor=0;
public:
    unsigned droppedFrames=0;
    explicit WindowsAudio(UINT deviceId=WAVE_MAPPER){
        WAVEFORMATEX format{};format.wFormatTag=WAVE_FORMAT_PCM;format.nChannels=2;format.nSamplesPerSec=48000;
        format.wBitsPerSample=16;format.nBlockAlign=4;format.nAvgBytesPerSec=192000;
        if(waveOutOpen(&device,deviceId,&format,0,0,CALLBACK_NULL)!=MMSYSERR_NOERROR){device=nullptr;return;}
        for(auto& buffer:buffers){buffer.header.lpData=reinterpret_cast<char*>(buffer.samples.data());buffer.header.dwBufferLength=sizeof(buffer.samples);
            buffer.prepared=waveOutPrepareHeader(device,&buffer.header,sizeof(WAVEHDR))==MMSYSERR_NOERROR;}
    }
    WindowsAudio(const WindowsAudio&)=delete;
    WindowsAudio& operator=(const WindowsAudio&)=delete;
    ~WindowsAudio(){if(device){waveOutReset(device);for(auto& buffer:buffers)if(buffer.prepared)waveOutUnprepareHeader(device,&buffer.header,sizeof(WAVEHDR));waveOutClose(device);}}
    bool available() const{return device!=nullptr;}
    void discardQueued(){if(device)waveOutReset(device);cursor=0;}
    void submit(const std::vector<int16_t>& samples){
        if(!device)return;auto& buffer=buffers[cursor];
        if(!buffer.prepared||(buffer.header.dwFlags&WHDR_INQUEUE)||samples.size()>buffer.samples.size()){++droppedFrames;return;}
        std::copy(samples.begin(),samples.end(),buffer.samples.begin());buffer.header.dwBufferLength=static_cast<DWORD>(samples.size()*sizeof(int16_t));
        if(waveOutWrite(device,&buffer.header,sizeof(WAVEHDR))==MMSYSERR_NOERROR)cursor=(cursor+1)%buffers.size();else ++droppedFrames;
    }
};
}
