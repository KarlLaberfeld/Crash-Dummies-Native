#pragma once
#include "ui.h"
#include <algorithm>
#include <fstream>
namespace ticd {
// Output adapter for the production UI renderer. Inputs are native-owned
// semantic state and decoded assets, never an original screenshot or map.
inline void nativeUiFrame(const std::string& path,const std::array<uint8_t,Width*Height>& frame){
    if(std::any_of(frame.begin(),frame.end(),[](int shade){return shade>3;}))throw std::runtime_error("Invalid native frame shade");
    std::ofstream out(path,std::ios::binary);if(!out.write(reinterpret_cast<const char*>(frame.data()),frame.size()))throw std::runtime_error("Cannot write native frame diagnostic");
}
}
